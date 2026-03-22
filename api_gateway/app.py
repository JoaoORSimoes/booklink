from flask import Flask, request, jsonify
import requests

from auth import create_token, auth_middleware
from proxy import proxy_request

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "api_gateway running"}), 200

@app.route("/login", methods=["POST"])
def login():
    resp = requests.post(
        "http://user_service:6000/api/users/login",
        json=request.json,
        timeout=5
    )

    if resp.status_code != 200:
        return jsonify(resp.json()), resp.status_code

    user = resp.json()
    token = create_token(user)
    return jsonify({"access_token": token}), 200

@app.before_request
def check_auth():
    if request.path in ("/login", "/health"):
        return
    return auth_middleware()

@app.route("/<service>/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@app.route("/<service>/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def gateway_proxy(service, path):
    return proxy_request(service, path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
