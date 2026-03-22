import hashlib
from flask import Blueprint, request, jsonify
from db import SessionLocal
from sqlalchemy.exc import SQLAlchemyError

from model import User
from sqlalchemy.orm import Session

user_bp = Blueprint("users", __name__)

@user_bp.route("/", methods=["GET"])
def list_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        return jsonify([u.to_dict() for u in users])
    finally:
        db.close()

@user_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify(user.to_dict())
    finally:
        db.close()

@user_bp.route("/", methods=["POST"])
def create_user():
    data = request.json or {}
    required = {"name", "email", "password"}
    if not required.issubset(data.keys()):
        return jsonify({"error": "Missing fields"}), 400

    db = SessionLocal()
    try:
        user = User(
            name=data["name"],
            email=data["email"],
            password=_hash_password(data["password"]),
            role=data.get("role", "student")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return jsonify(user.to_dict()), 201
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@user_bp.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        db.delete(user)
        db.commit()
        return jsonify({"message": "User deleted"})
    finally:
        db.close()


def _hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

@user_bp.route("/login", methods=["POST"])
def login():
    data = request.json or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.active:
            return jsonify({"error": "invalid credentials"}), 401

        if user.password != _hash_password(password):
            return jsonify({"error": "invalid credentials"}), 401

        return jsonify({
            "id": user.id,
            "email": user.email,
            "role": user.role
        })
    finally:
        db.close()