from flask import request, abort

def get_current_user():
    user_id = request.headers.get("X-User-Id")
    user_role = request.headers.get("X-User-Role")
    user_email = request.headers.get("X-User-Email")

    if not user_id or not user_role:
        abort(403, "missing user identity")

    return {
        "id": int(user_id),
        "role": user_role,
        "email": user_email,
    }