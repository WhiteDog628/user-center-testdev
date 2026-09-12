import requests
import time

import requests

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