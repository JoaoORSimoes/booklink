import jwt
from flask import request, jsonify

SECRET_KEY = "super-secret-key"
ALGORITHM = "HS256"


def create_token(user: dict) -> str:
    return jwt.encode(
        {
            "sub": user["id"],
            "email": user["email"],
            "role": user["role"],
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def auth_middleware():
    auth = request.headers.get("Authorization")

    if not auth or not auth.startswith("Bearer "):
        return jsonify({"error": "missing token"}), 401

    token = auth.split(" ", 1)[1]

    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        request.headers.environ["HTTP_X_USER_ID"] = str(decoded["sub"])
        request.headers.environ["HTTP_X_USER_ROLE"] = decoded["role"].lower()
        request.headers.environ["HTTP_X_USER_EMAIL"] = decoded.get("email", "")

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "invalid token"}), 401
