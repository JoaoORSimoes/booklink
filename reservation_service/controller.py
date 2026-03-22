import os
import requests
from flask import Blueprint, request, jsonify, current_app, abort
from sqlalchemy.exc import SQLAlchemyError
from db import SessionLocal
from datetime import datetime
from auth import get_current_user

from model import (
    ReservationItem,
    Reservation,
    ReservationStatus,
    ItemStatus,
)

reservations_bp = Blueprint("reservations", __name__)

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user_service:6000")
CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://catalog_service:7001")
STANDALONE = os.getenv("STANDALONE_MODE", "false").lower() == "true"

# external services helpers that propagate user identity via headers.
def _forward_headers():
    return {
        "X-User-Id": request.headers.get("X-User-Id"),
        "X-User-Role": request.headers.get("X-User-Role"),
        "X-User-Email": request.headers.get("X-User-Email"),
    }


def get_exemplar_info(exemplar_id):
    if STANDALONE:
        return {"available": False}

    try:
        resp = requests.get(
            f"{CATALOG_SERVICE_URL}/exemplars/{exemplar_id}",
            headers=_forward_headers(),
            timeout=3,
        )
        if resp.status_code != 200:
            return None
        return resp.json()
    except requests.exceptions.RequestException as e:
        current_app.logger.warning("get_exemplar_info failed: %s", e)
        return None


def notify_user_for_item(user_id, exemplar_id):
    current_app.logger.info(
        "Notify user %s: exemplar %s is available", user_id, exemplar_id
    )
    return True


# internal helpers
def reserve_position_for_exemplar(db, exemplar_id):
    q = (
        db.query(ReservationItem)
        .filter(
            ReservationItem.exemplar_id == exemplar_id,
            ReservationItem.cancelled == False,
        )
    )
    last = q.order_by(ReservationItem.position.desc()).first()
    return (last.position if last else 0) + 1


#endpoints
@reservations_bp.route("/", methods=["POST"])
def create_reservation():
    user = get_current_user()

    # only students can create reservations
    if user["role"] != "student":
        return jsonify({"error": "only students can create reservations"}), 403

    body = request.json or {}
    items = body.get("items")

    if not isinstance(items, list) or not items:
        return jsonify({"error": "items must be a non-empty list"}), 400

    db = SessionLocal()
    try:
        reservation = Reservation(
            user_id=user["id"],
            status=ReservationStatus.ACTIVE,
        )
        db.add(reservation)
        db.flush()  # get ID

        for it in items:
            exemplar_id = int(it.get("exemplar_id"))
            info = get_exemplar_info(exemplar_id)

            if info is None and not STANDALONE:
                db.rollback()
                return jsonify(
                    {"error": f"Catalog unavailable for exemplar {exemplar_id}"}
                ), 502

            pos = reserve_position_for_exemplar(db, exemplar_id)
            ri = ReservationItem(
                reservation_id=reservation.id,
                exemplar_id=exemplar_id,
                position=pos,
                status=ItemStatus.PENDING,
            )
            db.add(ri)

        db.commit()
        db.refresh(reservation)
        return jsonify(reservation.to_dict()), 201

    except SQLAlchemyError:
        db.rollback()
        current_app.logger.exception("DB error creating reservation")
        return jsonify({"error": "internal database error"}), 500
    finally:
        db.close()


@reservations_bp.route("/", methods=["GET"])
def list_reservations():
    user = get_current_user()

    db = SessionLocal()
    try:
        q = db.query(Reservation)

        # students can only see their own reservations
        if user["role"] == "student":
            q = q.filter(Reservation.user_id == user["id"])

        res = [r.to_dict() for r in q.all()]
        return jsonify(res)
    finally:
        db.close()


@reservations_bp.route("/<int:res_id>", methods=["GET"])
def get_reservation(res_id):
    user = get_current_user()

    db = SessionLocal()
    try:
        r = db.query(Reservation).filter(Reservation.id == res_id).first()
        if not r:
            return jsonify({"error": "Reservation not found"}), 404

        if user["role"] != "staff" and r.user_id != user["id"]:
            return jsonify({"error": "forbidden"}), 403

        return jsonify(r.to_dict())
    finally:
        db.close()


@reservations_bp.route("/<int:res_id>/cancel", methods=["POST"])
def cancel_reservation(res_id):
    user = get_current_user()

    db = SessionLocal()
    try:
        r = db.query(Reservation).filter(Reservation.id == res_id).first()
        if not r:
            return jsonify({"error": "Reservation not found"}), 404

        if user["role"] != "staff" and r.user_id != user["id"]:
            return jsonify({"error": "forbidden"}), 403

        if r.status == ReservationStatus.CANCELLED:
            return jsonify({"error": "Already cancelled"}), 400

        for it in r.items:
            it.status = ItemStatus.CANCELLED
            it.cancelled = True
            db.add(it)

        r.status = ReservationStatus.CANCELLED
        db.add(r)

        db.commit()
        db.refresh(r)
        return jsonify(r.to_dict()), 200

    except SQLAlchemyError:
        db.rollback()
        current_app.logger.exception("DB error cancelling reservation")
        return jsonify({"error": "internal database error"}), 500
    finally:
        db.close()


@reservations_bp.route("/exemplar/<int:exemplar_id>/notify", methods=["POST"])
def notify_next_for_exemplar(exemplar_id):
    # internal call (catalog → reservation)
    get_current_user()

    db = SessionLocal()
    try:
        next_item = (
            db.query(ReservationItem)
            .filter(
                ReservationItem.exemplar_id == exemplar_id,
                ReservationItem.cancelled == False,
                ReservationItem.status == ItemStatus.PENDING,
            )
            .order_by(ReservationItem.position.asc())
            .first()
        )

        if not next_item:
            return jsonify({"message": "No pending reservations"}), 204

        next_item.status = ItemStatus.NOTIFIED
        next_item.notified_at = datetime.utcnow()
        db.add(next_item)

        res = db.query(Reservation).filter(
            Reservation.id == next_item.reservation_id
        ).first()
        res.status = ReservationStatus.NOTIFIED
        db.add(res)

        db.commit()
        db.refresh(next_item)

        notify_user_for_item(res.user_id, exemplar_id)
        return jsonify(next_item.to_dict()), 200

    except SQLAlchemyError:
        db.rollback()
        current_app.logger.exception("DB error notifying next")
        return jsonify({"error": "internal database error"}), 500
    finally:
        db.close()


@reservations_bp.route("/<int:res_id>/items/<int:item_id>/fulfill", methods=["POST"])
def fulfill_item(res_id, item_id):
    user = get_current_user()

    if user["role"] != "staff":
        return jsonify({"error": "only staff can fulfill reservations"}), 403

    db = SessionLocal()
    try:
        item = (
            db.query(ReservationItem)
            .filter(
                ReservationItem.id == item_id,
                ReservationItem.reservation_id == res_id,
            )
            .first()
        )

        if not item:
            return jsonify({"error": "Item not found"}), 404

        if item.status != ItemStatus.NOTIFIED:
            return jsonify({"error": "Item not in NOTIFIED state"}), 400

        item.status = ItemStatus.FULFILLED
        item.fulfilled_at = datetime.utcnow()
        db.add(item)

        res = db.query(Reservation).filter(Reservation.id == res_id).first()
        if all(i.status == ItemStatus.FULFILLED for i in res.items):
            res.status = ReservationStatus.FULFILLED
        db.add(res)

        db.commit()
        db.refresh(item)
        return jsonify(item.to_dict()), 200

    except SQLAlchemyError:
        db.rollback()
        current_app.logger.exception("DB error fulfilling item")
        return jsonify({"error": "internal database error"}), 500
    finally:
        db.close()
