#!/usr/bin/env bash

set -Eeuo pipefail

DEPLOY_DIR="$HOME/user-center-deploy"
IMAGE_REPO="ghcr.io/whitedog628/user-center-testdev"
TARGET_SHA="${1:-}"

STATE_FILE="$DEPLOY_DIR/.last_successful_image"
BOOTSTRAP_ROLLBACK_IMAGE="user-center-app:rollback-bootstrap"

SMOKE_USER=""
ROLLBACK_IMAGE=""

if [[ -z "$TARGET_SHA" ]]; then
    echo "Usage: $0 <git-sha>"
    exit 2
fi

TARGET_IMAGE="${IMAGE_REPO}:${TARGET_SHA}"

cd "$DEPLOY_DIR"

# Load deployment environment variables.
set -a
source .env
set +a


cleanup_smoke_user() {
    if [[ -n "${SMOKE_USER:-}" ]]; then
        echo "Cleaning smoke-test user..."

        docker compose exec -T \
            -e MYSQL_PWD="$DB_PASSWORD" \
            mysql \
            mysql \
            -u"$DB_USER" \
            "$DB_NAME" \
            -e "DELETE FROM users WHERE username='${SMOKE_USER}';" \
            >/dev/null 2>&1 || true
    fi
}


wait_for_health() {
    echo "Waiting for application health check..."

    for i in {1..30}; do
        if curl -fsS \
            http://127.0.0.1:5000/health \
            >/dev/null; then

            echo "Application is healthy."
            return 0
        fi

        echo "Health check attempt $i/30 failed."
        sleep 2
    done

    echo "Application failed health check."
    return 1
}


rollback() {
    local exit_code=$?

    trap - ERR

    echo
    echo "Deployment failed."
    echo "Starting rollback..."

    if [[ -z "$ROLLBACK_IMAGE" ]]; then
        echo "No rollback image is available."
        docker compose logs --no-color app || true
        exit "$exit_code"
    fi

    echo "Rollback image: $ROLLBACK_IMAGE"

    if ! docker image inspect \
        "$ROLLBACK_IMAGE" \
        >/dev/null 2>&1; then

        echo "Rollback image not found locally."
        echo "Trying to pull rollback image..."

        docker pull "$ROLLBACK_IMAGE" || true
    fi

    APP_IMAGE="$ROLLBACK_IMAGE" \
        docker compose up \
        -d \
        --no-deps \
        --force-recreate \
        --pull never \
        app

    if wait_for_health; then
        echo "Rollback completed successfully."
    else
        echo "Rollback container is not healthy."
        docker compose logs --no-color app || true
    fi

    exit "$exit_code"
}


trap cleanup_smoke_user EXIT
trap rollback ERR


echo "========================================"
echo "User Center Deployment"
echo "========================================"
echo "Target image: $TARGET_IMAGE"


# Determine rollback target.
if [[ -f "$STATE_FILE" ]]; then
    ROLLBACK_IMAGE="$(cat "$STATE_FILE")"

    echo "Previous successful image:"
    echo "$ROLLBACK_IMAGE"

elif docker inspect \
    user-center-app \
    >/dev/null 2>&1; then

    echo "No deployment state file found."
    echo "Saving current container image as bootstrap rollback image."

    CURRENT_IMAGE_ID="$(
        docker inspect \
            -f '{{.Image}}' \
            user-center-app
    )"

    docker tag \
        "$CURRENT_IMAGE_ID" \
        "$BOOTSTRAP_ROLLBACK_IMAGE"

    ROLLBACK_IMAGE="$BOOTSTRAP_ROLLBACK_IMAGE"
fi


# Pull immutable image built for this Git commit.
echo
echo "Pulling target image..."

docker pull "$TARGET_IMAGE"


# Deploy only the application container.
# MySQL and its persistent volume are not recreated.
echo
echo "Deploying application..."

APP_IMAGE="$TARGET_IMAGE" \
    docker compose up \
    -d \
    --no-deps \
    --force-recreate \
    --pull never \
    app


# Health check.
wait_for_health


# Smoke test: register.
echo
echo "Running smoke tests..."

SMOKE_ID="$(date +%s%N)"
SMOKE_USER="smoke_${SMOKE_ID}"
SMOKE_EMAIL="smoke_${SMOKE_ID}@example.com"
SMOKE_PASSWORD="SmokeTest123456"

REGISTER_STATUS="$(
    curl -sS \
        -o /tmp/user-center-register.json \
        -w "%{http_code}" \
        -X POST \
        http://127.0.0.1:5000/api/register \
        -H "Content-Type: application/json" \
        -d "{
            \"username\":\"${SMOKE_USER}\",
            \"password\":\"${SMOKE_PASSWORD}\",
            \"email\":\"${SMOKE_EMAIL}\"
        }"
)"

if [[ "$REGISTER_STATUS" != "201" ]]; then
    echo "Register smoke test failed."
    echo "HTTP status: $REGISTER_STATUS"
    cat /tmp/user-center-register.json
    false
fi

echo "Register smoke test passed."


# Smoke test: login.
LOGIN_STATUS="$(
    curl -sS \
        -o /tmp/user-center-login.json \
        -w "%{http_code}" \
        -X POST \
        http://127.0.0.1:5000/api/login \
        -H "Content-Type: application/json" \
        -d "{
            \"username\":\"${SMOKE_USER}\",
            \"password\":\"${SMOKE_PASSWORD}\"
        }"
)"

if [[ "$LOGIN_STATUS" != "200" ]]; then
    echo "Login smoke test failed."
    echo "HTTP status: $LOGIN_STATUS"
    cat /tmp/user-center-login.json
    false
fi

echo "Login smoke test passed."


ACCESS_TOKEN="$(
    python3 -c "
import json

with open(
    '/tmp/user-center-login.json',
    encoding='utf-8'
) as f:
    print(json.load(f)['access_token'])
"
)"


# Smoke test: authenticated profile.
PROFILE_STATUS="$(
    curl -sS \
        -o /tmp/user-center-profile.json \
        -w "%{http_code}" \
        http://127.0.0.1:5000/api/user/profile \
        -H "Authorization: Bearer ${ACCESS_TOKEN}"
)"

if [[ "$PROFILE_STATUS" != "200" ]]; then
    echo "Profile smoke test failed."
    echo "HTTP status: $PROFILE_STATUS"
    cat /tmp/user-center-profile.json
    false
fi

echo "Profile smoke test passed."


# Record immutable version only after every validation passes.
printf '%s\n' \
    "$TARGET_IMAGE" \
    > "$STATE_FILE"

echo
echo "========================================"
echo "Deployment successful."
echo "Deployed image:"
echo "$TARGET_IMAGE"
echo "========================================"
