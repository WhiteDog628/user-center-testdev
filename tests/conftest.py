import os

import pymysql
import pytest
from dotenv import load_dotenv


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