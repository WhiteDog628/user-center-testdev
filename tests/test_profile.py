import requests
import time
import pytest

BASE_URL = "http://127.0.0.1:5000"

def test_get_profile_success(auth_user):
    token = auth_user["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f"{BASE_URL}/api/user/profile",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == auth_user["id"]
    assert data["username"] == auth_user["username"]
    assert data["email"] == auth_user["email"]
    
def test_get_profile_without_token():
    response = requests.get(
        f"{BASE_URL}/api/user/profile"
    )

    assert response.status_code == 401

    data = response.json()

    assert data["msg"] == "Missing Authorization Header"
    
def test_update_profile_success(auth_user, db_connection):
    token = auth_user["access_token"]

    new_email = (
        f"updated_{time.time_ns()}@example.com"
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    payload = {
        "email": new_email
    }

    response = requests.put(
        f"{BASE_URL}/api/user/profile",
        headers=headers,
        json=payload
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "profile updated successfully"
    assert data["username"] == auth_user["username"]
    assert data["email"] == new_email

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT username, email
            FROM users
            WHERE username = %s
            """,
            (auth_user["username"],)
        )

        user = cursor.fetchone()

    assert user is not None
    assert user["email"] == new_email


def test_update_profile_without_token():
    payload = {
        "email": "no_token@example.com"
    }

    response = requests.put(
        f"{BASE_URL}/api/user/profile",
        json=payload
    )

    assert response.status_code == 401

    data = response.json()

    assert data["msg"] == "Missing Authorization Header"


def test_update_profile_missing_fields(auth_user):
    token = auth_user["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    payload = {
        "other_field": "test"
    }

    response = requests.put(
        f"{BASE_URL}/api/user/profile",
        headers=headers,
        json=payload
    )

    assert response.status_code == 400

    data = response.json()

    assert data["message"] == "username or email is required"
    
def test_update_profile_duplicate_email(auth_user, other_user):
    headers = {
        "Authorization": f"Bearer {auth_user['access_token']}"
    }

    payload = {
        "email": other_user["email"]
    }

    response = requests.put(
        f"{BASE_URL}/api/user/profile",
        headers=headers,
        json=payload
    )

    assert response.status_code == 409

    data = response.json()

    assert data["message"] == "email already exists"


def test_update_profile_duplicate_username(auth_user, other_user):
    headers = {
        "Authorization": f"Bearer {auth_user['access_token']}"
    }

    payload = {
        "username": other_user["username"]
    }

    response = requests.put(
        f"{BASE_URL}/api/user/profile",
        headers=headers,
        json=payload
    )

    assert response.status_code == 409

    data = response.json()

    assert data["message"] == "username already exists"


def test_update_profile_same_values(auth_user):
    headers = {
        "Authorization": f"Bearer {auth_user['access_token']}"
    }

    payload = {
        "username": auth_user["username"],
        "email": auth_user["email"]
    }

    response = requests.put(
        f"{BASE_URL}/api/user/profile",
        headers=headers,
        json=payload
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "profile updated successfully"
    assert data["username"] == auth_user["username"]
    assert data["email"] == auth_user["email"]
    
@pytest.mark.parametrize(
    "username_length, expected_status, expected_message",
    [
        (50, 200, "profile updated successfully"),
        (51, 400, "username must be at most 50 characters"),
    ]
)
def test_update_profile_username_length_boundary(
    auth_user,
    cleanup_users,
    username_length,
    expected_status,
    expected_message
):
    token = auth_user["access_token"]

    new_username = "u" * username_length

    # 50 字符场景会真的修改数据库中的 username，
    # 因此需要把新 username 也加入清理列表
    if expected_status == 200:
        cleanup_users.append(new_username)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    payload = {
        "username": new_username
    }

    response = requests.put(
        f"{BASE_URL}/api/user/profile",
        headers=headers,
        json=payload
    )

    assert response.status_code == expected_status

    data = response.json()

    assert data["message"] == expected_message


@pytest.mark.parametrize(
    "email_length, expected_status, expected_message",
    [
        (120, 200, "profile updated successfully"),
        (121, 400, "email must be at most 120 characters"),
    ]
)
def test_update_profile_email_length_boundary(
    auth_user,
    email_length,
    expected_status,
    expected_message
):
    token = auth_user["access_token"]

    domain = "@example.com"
    local_part_length = email_length - len(domain)

    email = (
        "a" * local_part_length
        + domain
    )

    assert len(email) == email_length

    headers = {
        "Authorization": f"Bearer {token}"
    }

    payload = {
        "email": email
    }

    response = requests.put(
        f"{BASE_URL}/api/user/profile",
        headers=headers,
        json=payload
    )

    assert response.status_code == expected_status

    data = response.json()

    assert data["message"] == expected_message
    
def test_update_profile_non_json_body(auth_user):
    headers = {
        "Authorization": (
            f"Bearer {auth_user['access_token']}"
        ),
        "Content-Type": "text/plain"
    }

    response = requests.put(
        f"{BASE_URL}/api/user/profile",
        headers=headers,
        data="not-json"
    )

    assert response.status_code == 400

    data = response.json()

    assert data["message"] == "request body must be JSON"