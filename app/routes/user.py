from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.user import User
from ..utils.decorators import admin_required

user_bp = Blueprint("user", __name__)


def _err(msg, code):
    return jsonify({"success": False, "error": msg}), code


def _ok(data, code=200):
    return jsonify({"success": True, "data": data}), code


@user_bp.get("/me")
@jwt_required()
def get_me():
    user = User.query.get(int(get_jwt_identity()))
    return _ok(user.to_dict())


@user_bp.put("/me")
@jwt_required()
def update_me():
    user = User.query.get(int(get_jwt_identity()))
    body = request.get_json(silent=True) or {}

    new_username = body.get("username", "").strip()
    new_email = body.get("email", "").strip().lower()

    if new_username:
        existing = User.query.filter_by(username=new_username).first()
        if existing and existing.id != user.id:
            return _err("username already taken", 409)
        user.username = new_username

    if new_email:
        existing = User.query.filter_by(email=new_email).first()
        if existing and existing.id != user.id:
            return _err("email already registered", 409)
        user.email = new_email

    db.session.commit()
    return _ok(user.to_dict())


@user_bp.put("/me/password")
@jwt_required()
def change_password():
    user = User.query.get(int(get_jwt_identity()))
    body = request.get_json(silent=True) or {}

    current = body.get("current_password", "")
    new_pw = body.get("new_password", "")

    if not current or not new_pw:
        return _err("current_password and new_password are required", 400)
    if not user.check_password(current):
        return _err("current password is incorrect", 401)
    if len(new_pw) < 6:
        return _err("new password must be at least 6 characters", 400)

    user.set_password(new_pw)
    db.session.commit()
    return _ok({"message": "password updated"})


@user_bp.get("/")
@admin_required
def list_users():
    users = User.query.all()
    return _ok([u.to_dict() for u in users])


@user_bp.put("/<int:user_id>/role")
@admin_required
def set_role(user_id):
    body = request.get_json(silent=True) or {}
    role = body.get("role", "")

    if role not in ("user", "admin"):
        return _err("role must be 'user' or 'admin'", 400)

    user = User.query.get(user_id)
    if not user:
        return _err("user not found", 404)

    user.role = role
    db.session.commit()
    return _ok(user.to_dict())
