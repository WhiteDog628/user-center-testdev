import time

import requests

from werkzeug.security import check_password_hash

BASE_URL = "http://127.0.0.1:5000"

def test_login_success(cleanup_users):
    timestamp = int(time.time())

    username = f"login_user_{timestamp}"
    password = "Test123456"
    email = f"login_{timestamp}@example.com"

    cleanup_users.append(username)

    register_payload = {
        "username": username,
        "password": password,
        "email": email
    }

    register_response = requests.post(
        f"{BASE_URL}/api/register",
        json=register_payload
    )

    assert register_response.status_code == 201

    login_payload = {
        "username": username,
        "password": password
    }

    login_response = requests.post(
        f"{BASE_URL}/api/login",
        json=login_payload
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert data["message"] == "login successful"
    assert data["username"] == username
    assert "id" in data
    assert "access_token" in data
    assert data["access_token"]
    
def test_login_wrong_password(cleanup_users):
    timestamp = int(time.time())

    username = f"login_wrong_pwd_{timestamp}"
    password = "Test123456"
    email = f"login_wrong_pwd_{timestamp}@example.com"

    cleanup_users.append(username)

    register_payload = {
        "username": username,
        "password": password,
        "email": email
    }

    register_response = requests.post(
        f"{BASE_URL}/api/register",
        json=register_payload
    )

    assert register_response.status_code == 201

    login_payload = {
        "username": username,
        "password": "WrongPassword"
    }

    login_response = requests.post(
        f"{BASE_URL}/api/login",
        json=login_payload
    )

    assert login_response.status_code == 401

    data = login_response.json()

    assert data["message"] == "invalid username or password"

def test_login_user_not_found():
    timestamp = int(time.time())

    login_payload = {
        "username": f"not_exist_user_{timestamp}",
        "password": "Test123456"
    }

    login_response = requests.post(
        f"{BASE_URL}/api/login",
        json=login_payload
    )

    assert login_response.status_code == 401

    data = login_response.json()

    assert data["message"] == "invalid username or password"
    
def test_login_missing_password():
    payload = {
        "username": "test_user"
    }

    response = requests.post(
        f"{BASE_URL}/api/login",
        json=payload
    )

    assert response.status_code == 400

    data = response.json()

    assert data["message"] == "username and password are required"
    
def test_login_database_validation(cleanup_users, db_connection):
    timestamp = time.time_ns()

    username = f"login_db_user_{timestamp}"
    password = "Test123456"
    email = f"login_db_user_{timestamp}@example.com"

    cleanup_users.append(username)

    register_payload = {
        "username": username,
        "password": password,
        "email": email
    }

    register_response = requests.post(
        f"{BASE_URL}/api/register",
        json=register_payload
    )

    assert register_response.status_code == 201

    login_payload = {
        "username": username,
        "password": password
    }

    login_response = requests.post(
        f"{BASE_URL}/api/login",
        json=login_payload
    )

    assert login_response.status_code == 200

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