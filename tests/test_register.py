import time

import requests

from werkzeug.security import check_password_hash

BASE_URL = "http://127.0.0.1:5000"

def test_register_success(cleanup_users):
    timestamp = int(time.time())

    payload = {
        "username": f"auto_user_{timestamp}",
        "password": "Test123456",
        "email": f"auto_{timestamp}@example.com"
    }
    cleanup_users.append(payload["username"])

    response = requests.post(
        f"{BASE_URL}/api/register",
        json=payload
    )

    assert response.status_code == 201

    data = response.json()

    assert data["message"] == "user registered successfully"
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert "id" in data
    assert "password" not in data
    
def test_register_missing_password():
    payload = {
        "username": "auto_missing_password",
        "email": "missing_password@example.com"
    }

    response = requests.post(
        f"{BASE_URL}/api/register",
        json=payload
    )

    assert response.status_code == 400

    data = response.json()

    assert data["message"] == "username, password and email are required"
    
def test_register_duplicate_username(cleanup_users):
    timestamp = int(time.time())

    username = f"duplicate_user_{timestamp}"
    cleanup_users.append(username)

    first_payload = {
        "username": username,
        "password": "Test123456",
        "email": f"duplicate_first_{timestamp}@example.com"
    }

    second_payload = {
        "username": username,
        "password": "Test123456",
        "email": f"duplicate_second_{timestamp}@example.com"
    }

    first_response = requests.post(
        f"{BASE_URL}/api/register",
        json=first_payload
    )

    assert first_response.status_code == 201

    second_response = requests.post(
        f"{BASE_URL}/api/register",
        json=second_payload
    )

    assert second_response.status_code == 409

    data = second_response.json()

    assert data["message"] == "username already exists"
    
def test_register_duplicate_email(cleanup_users):
    timestamp = int(time.time())

    email = f"duplicate_email_{timestamp}@example.com"

    first_payload = {
        "username": f"email_user_first_{timestamp}",
        "password": "Test123456",
        "email": email
    }

    second_payload = {
        "username": f"email_user_second_{timestamp}",
        "password": "Test123456",
        "email": email
    }
    
    cleanup_users.append(first_payload["username"])

    first_response = requests.post(
        f"{BASE_URL}/api/register",
        json=first_payload
    )

    assert first_response.status_code == 201

    second_response = requests.post(
        f"{BASE_URL}/api/register",
        json=second_payload
    )

    assert second_response.status_code == 409

    data = second_response.json()

    assert data["message"] == "email already exists"
    
    
def test_register_database_persistence(cleanup_users, db_connection):
    timestamp = time.time_ns()

    username = f"db_user_{timestamp}"
    password = "Test123456"
    email = f"db_user_{timestamp}@example.com"

    cleanup_users.append(username)

    payload = {
        "username": username,
        "password": password,
        "email": email
    }

    response = requests.post(
        f"{BASE_URL}/api/register",
        json=payload
    )

    assert response.status_code == 201

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, username, email, password_hash
            FROM users
            WHERE username = %s
            """,
            (username,)
        )

        user = cursor.fetchone()

    assert user is not None
    assert user["username"] == username
    assert user["email"] == email
    assert user["password_hash"] != password
    assert check_password_hash(
        user["password_hash"],
        password
    )