import os
import uuid
import requests
from flask import Blueprint, request, jsonify, current_app, abort
from db import SessionLocal

from model import PaymentModel, PaymentStatus
from auth import get_current_user

payments_bp = Blueprint("payments", __name__)

ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order_service:3000")


def _forward_headers():
    return {
        "X-User-Id": request.headers.get("X-User-Id"),
        "X-User-Role": request.headers.get("X-User-Role"),
        "X-User-Email": request.headers.get("X-User-Email"),
    }


# =========================================================
# EXTERNAL SERVICE HELPERS
# =========================================================
def verify_order(reservation_id):
    try:
        resp = requests.get(
            f"{ORDER_SERVICE_URL}/reservations/{reservation_id}",
            headers=_forward_headers(),
            timeout=3,
        )
        return resp.status_code == 200
    except requests.exceptions.RequestException as e:
        current_app.logger.warning("verify_order failed: %s", e)
        return False


def notify_order_paid(reservation_id, payment_id):
    try:
        resp = requests.post(
            f"{ORDER_SERVICE_URL}/reservations/{reservation_id}/pay",
            json={"payment_id": payment_id},
            headers=_forward_headers(),
            timeout=3,
        )
        return resp.status_code in (200, 204)
    except requests.exceptions.RequestException as e:
        current_app.logger.warning("notify_order_paid failed: %s", e)
        return False


# =========================================================
# ENDPOINTS
# =========================================================
@payments_bp.route("/", methods=["POST"])
def create_payment():
    user = get_current_user()

    # Apenas students podem pagar
    if user["role"] != "student":
        return jsonify({"error": "only students can create payments"}), 403

    body = request.json or {}
    for k in ("reservation_id", "amount", "method"):
        if k not in body:
            return jsonify({"error": f"Missing '{k}'"}), 400

    reservation_id = int(body["reservation_id"])
    amount = float(body["amount"])
    method = body["method"]

    if amount <= 0:
        return jsonify({"error": "Amount must be > 0"}), 400

    if not verify_order(reservation_id):
        return jsonify({"error": "Reservation not found or order service unavailable"}), 404

    db = SessionLocal()
    try:
        payment = PaymentModel(
            reservation_id=reservation_id,
            user_id=user["id"],  # 👈 identidade confiável
            amount=amount,
            method=method,
            status=PaymentStatus.PENDING,
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        # Simulação de pagamento bem-sucedido
        payment.status = PaymentStatus.COMPLETED
        payment.txn_id = f"SIM-{payment.id}-{uuid.uuid4().hex[:8]}"
        db.add(payment)
        db.commit()
        db.refresh(payment)

        notify_order_paid(reservation_id, payment.id)

        return jsonify(payment.to_dict()), 201

    except Exception:
        db.rollback()
        current_app.logger.exception("Erro criando pagamento")
        return jsonify({"error": "Internal error"}), 500
    finally:
        db.close()


@payments_bp.route("/<int:payment_id>", methods=["GET"])
def get_payment(payment_id):
    user = get_current_user()

    db = SessionLocal()
    try:
        p = db.query(PaymentModel).filter(PaymentModel.id == payment_id).first()
        if not p:
            return jsonify({"error": "Payment not found"}), 404

        # student só pode ver os próprios pagamentos
        if user["role"] != "staff" and p.user_id != user["id"]:
            return jsonify({"error": "forbidden"}), 403

        return jsonify(p.to_dict())
    finally:
        db.close()


@payments_bp.route("/", methods=["GET"])
def list_payments():
    user = get_current_user()

    db = SessionLocal()
    try:
        q = db.query(PaymentModel)

        # student vê apenas os próprios pagamentos
        if user["role"] == "student":
            q = q.filter(PaymentModel.user_id == user["id"])

        results = [p.to_dict() for p in q.all()]
        return jsonify(results)
    finally:
        db.close()


@payments_bp.route("/<int:payment_id>/refund", methods=["POST"])
def refund_payment(payment_id):
    user = get_current_user()

    # Apenas staff pode reembolsar
    if user["role"] != "staff":
        return jsonify({"error": "only staff can refund payments"}), 403

    db = SessionLocal()
    try:
        p = db.query(PaymentModel).filter(PaymentModel.id == payment_id).first()
        if not p:
            return jsonify({"error": "Payment not found"}), 404

        if p.status != PaymentStatus.COMPLETED:
            return jsonify({"error": "Only completed payments can be refunded"}), 400

        p.status = PaymentStatus.REFUNDED
        db.add(p)
        db.commit()
        db.refresh(p)

        return jsonify(p.to_dict()), 200

    finally:
        db.close()
