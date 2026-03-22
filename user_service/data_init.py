# user_service/data_init.py
from db import SessionLocal
from sqlalchemy.exc import SQLAlchemyError
import hashlib

from model import User


def _hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def seed_data():
    db = SessionLocal()
    try:
        exists = db.query(User).first()
        if exists:
            print("user_service: users already exist, skipping seed.")
            return

        users = []
        for i in range(1, 21):
            u = User(
                name=f"User {i}",
                email=f"user{i}@example.com",
                password=_hash_password("password123"),  # hashed for demo
                role="student" if i % 3 != 0 else "staff"
            )
            users.append(u)
            db.add(u)

        db.commit()
        print("user_service: seeded 20 users.")
    except SQLAlchemyError as e:
        db.rollback()
        print("user_service: error seeding users:", e)
    finally:
        db.close()
