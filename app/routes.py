from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import User

api = Blueprint("api", __name__, url_prefix="/api")

@api.post("/register")
def register():
    data = request.get_json(silent=True)

    if not data:
        return {
            "message": "request body must be JSON"
        }, 400

    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    if not username or not password or not email:
        return {
            "message": "username, password and email are required"
        }, 400

    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        return {
            "message": "username already exists"
        }, 409

    existing_email = User.query.filter_by(email=email).first()

    if existing_email:
        return {
            "message": "email already exists"
        }, 409

    user = User(
        username=username,
        email=email
    )

    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()

        return {
            "message": "database error"
        }, 500

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "message": "user registered successfully"
    }, 201


@api.post("/login")
def login():
    data = request.get_json(silent=True)

    if not data:
        return {
            "message": "request body must be JSON"
        }, 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return {
            "message": "username and password are required"
        }, 400

    user = User.query.filter_by(username=username).first()

    if not user:
        return {
            "message": "invalid username or password"
        }, 401

    if not user.check_password(password):
        return {
            "message": "invalid username or password"
        }, 401
        
    access_token = create_access_token(
    identity=str(user.id)
    )
    
    return {
        "id": user.id,
        "username": user.username,
        "access_token": access_token,
        "message": "login successful"
    }, 200
    
@api.get("/user/profile")
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()

    user = db.session.get(User, int(user_id))

    if not user:
        return {
            "message": "user not found"
        }, 404

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email
    }, 200
    
@api.put("/user/profile")
@jwt_required()
def update_profile():
    data = request.get_json(silent=True)

    if not data:
        return {
            "message": "request body must be JSON"
        }, 400

    username = data.get("username")
    email = data.get("email")

    if not username and not email:
        return {
            "message": "username or email is required"
        }, 400

    user_id = get_jwt_identity()

    user = db.session.get(User, int(user_id))

    if not user:
        return {
            "message": "user not found"
        }, 404

    if username:
        existing_user = User.query.filter(
            User.username == username,
            User.id != user.id
        ).first()

        if existing_user:
            return {
                "message": "username already exists"
            }, 409

        user.username = username

    if email:
        existing_email = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()

        if existing_email:
            return {
                "message": "email already exists"
            }, 409

        user.email = email

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()

        return {
            "message": "database error"
        }, 500

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "message": "profile updated successfully"
    }, 200