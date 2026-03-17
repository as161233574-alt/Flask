from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from ..extensions import db
from ..models.user import User, TokenBlocklist

auth_bp = Blueprint("auth", __name__)


def _err(msg, code):
    return jsonify({"success": False, "error": msg}), code


def _ok(data, code=200):
    return jsonify({"success": True, "data": data}), code


@auth_bp.post("/register")
def register():
    body = request.get_json(silent=True) or {}
    username = body.get("username", "").strip()
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")

    if not username or not email or not password:
        return _err("username, email and password are required", 400)
    if len(password) < 6:
        return _err("password must be at least 6 characters", 400)
    if User.query.filter_by(username=username).first():
        return _err("username already taken", 409)
    if User.query.filter_by(email=email).first():
        return _err("email already registered", 409)

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return _ok(user.to_dict(), 201)


@auth_bp.post("/login")
def login():
    body = request.get_json(silent=True) or {}
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")

    if not email or not password:
        return _err("email and password are required", 400)

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return _err("invalid credentials", 401)

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    return _ok({"access_token": access_token, "refresh_token": refresh_token})


@auth_bp.post("/logout")
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    db.session.add(TokenBlocklist(jti=jti))
    db.session.commit()
    return _ok({"message": "logged out"})


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return _ok({"access_token": access_token})
