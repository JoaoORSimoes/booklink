import requests
from flask import request, Response, jsonify

SERVICE_MAP = {
    "users": "user_service:6000",
    "catalog": "catalog_service:7001",
    "reservations": "reservation_service:3100",
    "payments": "payment_service:4000",
}

def proxy_request(service, path):
    target = SERVICE_MAP.get(service)

    if not target:
        return jsonify({
            "error": f"Service '{service}' not found"
        }), 404

    # 🔥 Gateway ADICIONA /api/{service}
    url = f"http://{target}/api/{service}/{path}".rstrip("/")

    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }

    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.args,
            json=request.get_json(silent=True),
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "service unavailable",
            "details": str(e)
        }), 502

    return Response(
        resp.content,
        status=resp.status_code,
        headers=dict(resp.headers)
    )
