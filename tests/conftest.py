import os

import pymysql
import pytest
from dotenv import load_dotenv
import time

import requests

BASE_URL = "http://127.0.0.1:5000"
load_dotenv()


@pytest.fixture
def cleanup_users():
    usernames = []

    yield usernames

    if not usernames:
        return

    connection = pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        charset="utf8mb4",
        autocommit=True,
    )

    try:
        with connection.cursor() as cursor:
            placeholders = ", ".join(["%s"] * len(usernames))

            sql = (
                f"DELETE FROM users "
                f"WHERE username IN ({placeholders})"
            )

            cursor.execute(sql, usernames)

    finally:
        connection.close()
        
@pytest.fixture
def db_connection():
    connection = pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )

    yield connection

    connection.close()
    
@pytest.fixture
def auth_user(cleanup_users):
    timestamp = time.time_ns()

    username = f"auth_user_{timestamp}"
    password = "Test123456"
    email = f"auth_user_{timestamp}@example.com"

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

    login_data = login_response.json()

    return {
        "id": login_data["id"],
        "username": username,
        "password": password,
        "email": email,
        "access_token": login_data["access_token"]
    }

@pytest.fixture
def other_user(cleanup_users):
    timestamp = time.time_ns()

    username = f"other_user_{timestamp}"
    password = "Test123456"
    email = f"other_user_{timestamp}@example.com"

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

    data = response.json()

    return {
        "id": data["id"],
        "username": username,
        "password": password,
        "email": email
    }