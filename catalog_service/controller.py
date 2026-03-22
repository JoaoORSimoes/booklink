import os
import requests
from flask import Blueprint, request, jsonify, current_app, abort
from sqlalchemy.exc import SQLAlchemyError
from auth import get_current_user

from db import SessionLocal
from model import Book, Exemplar

catalog_bp = Blueprint("catalog", __name__)

RESERVATION_SERVICE_URL = os.getenv(
    "RESERVATION_SERVICE_URL", "http://reservation_service:3100"
)
STANDALONE = os.getenv("STANDALONE_MODE", "false").lower() == "true"


def _forward_headers():
    return {
        "X-User-Id": request.headers.get("X-User-Id"),
        "X-User-Role": request.headers.get("X-User-Role"),
        "X-User-Email": request.headers.get("X-User-Email"),
    }


# =========================================================
# INTERNAL / EXTERNAL HELPERS
# =========================================================
def notify_reservation_service_exemplar_available(exemplar_id: int) -> bool:
    if STANDALONE:
        current_app.logger.info(
            "STANDALONE: would notify reservation service for exemplar %s",
            exemplar_id,
        )
        return True
    try:
        url = f"{RESERVATION_SERVICE_URL}/reservations/exemplar/{exemplar_id}/notify"
        resp = requests.post(url, headers=_forward_headers(), timeout=3)
        return resp.status_code in (200, 204)
    except requests.exceptions.RequestException as e:
        current_app.logger.warning("Notify reservation failed: %s", e)
        return False


@catalog_bp.route("/books/", methods=["POST"])
def create_book():
    user = get_current_user()

    if user["role"] != "staff":
        return jsonify({"error": "only staff can create books"}), 403

    body = request.json or {}
    if "title" not in body:
        return jsonify({"error": "Missing 'title'"}), 400

    db = SessionLocal()
    try:
        book = Book(
            title=body["title"],
            authors=body.get("authors"),
            isbn=body.get("isbn"),
            publisher=body.get("publisher"),
            year=body.get("year"),
            description=body.get("description"),
        )
        db.add(book)
        db.commit()
        db.refresh(book)
        return jsonify(book.to_dict()), 201
    except SQLAlchemyError:
        db.rollback()
        current_app.logger.exception("DB error creating book")
        return jsonify({"error": "internal database error"}), 500
    finally:
        db.close()


@catalog_bp.route("/books/", methods=["GET"])
def list_books():
    get_current_user()  # qualquer utilizador autenticado

    q = request.args.get("q")
    include_exemplars = (
        request.args.get("include_exemplars", "false").lower() == "true"
    )
    db = SessionLocal()
    try:
        qset = db.query(Book)
        if q:
            qlike = f"%{q}%"
            qset = qset.filter(
                (Book.title.ilike(qlike))
                | (Book.authors.ilike(qlike))
                | (Book.isbn.ilike(qlike))
            )
        books = [
            b.to_dict(include_exemplars=include_exemplars)
            for b in qset.all()
        ]
        return jsonify(books)
    finally:
        db.close()


@catalog_bp.route("/books/<int:book_id>", methods=["GET"])
def get_book(book_id):
    get_current_user()

    include_exemplars = (
        request.args.get("include_exemplars", "false").lower() == "true"
    )
    db = SessionLocal()
    try:
        b = db.query(Book).filter(Book.id == book_id).first()
        if not b:
            return jsonify({"error": "Book not found"}), 404
        return jsonify(b.to_dict(include_exemplars=include_exemplars))
    finally:
        db.close()


@catalog_bp.route("/books/<int:book_id>", methods=["PATCH"])
def update_book(book_id):
    user = get_current_user()

    if user["role"] != "staff":
        return jsonify({"error": "only staff can update books"}), 403

    body = request.json or {}
    db = SessionLocal()
    try:
        b = db.query(Book).filter(Book.id == book_id).first()
        if not b:
            return jsonify({"error": "Book not found"}), 404
        for field in (
            "title",
            "authors",
            "isbn",
            "publisher",
            "year",
            "description",
        ):
            if field in body:
                setattr(b, field, body[field])
        db.add(b)
        db.commit()
        db.refresh(b)
        return jsonify(b.to_dict())
    except SQLAlchemyError:
        db.rollback()
        current_app.logger.exception("DB error updating book")
        return jsonify({"error": "internal database error"}), 500
    finally:
        db.close()


@catalog_bp.route("/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    user = get_current_user()

    if user["role"] != "staff":
        return jsonify({"error": "only staff can delete books"}), 403

    db = SessionLocal()
    try:
        b = db.query(Book).filter(Book.id == book_id).first()
        if not b:
            return jsonify({"error": "Book not found"}), 404
        db.delete(b)
        db.commit()
        return jsonify({"message": "Book deleted"}), 200
    except SQLAlchemyError:
        db.rollback()
        current_app.logger.exception("DB error deleting book")
        return jsonify({"error": "internal database error"}), 500
    finally:
        db.close()


# =========================================================
# EXEMPLARS
# =========================================================
@catalog_bp.route("/exemplars/", methods=["POST"])
def create_exemplar():
    user = get_current_user()

    if user["role"] != "staff":
        return jsonify({"error": "only staff can create exemplars"}), 403

    body = request.json or {}
    if "book_id" not in body:
        return jsonify({"error": "Missing 'book_id'"}), 400

    db = SessionLocal()
    try:
        b = db.query(Book).filter(Book.id == int(body["book_id"])).first()
        if not b:
            return jsonify({"error": "Book not found"}), 404

        ex = Exemplar(
            book_id=b.id,
            barcode=body.get("barcode"),
            available=body.get("available", True),
            location=body.get("location"),
            condition=body.get("condition"),
        )
        db.add(ex)
        db.commit()
        db.refresh(ex)
        return jsonify(ex.to_dict()), 201
    except SQLAlchemyError:
        db.rollback()
        current_app.logger.exception("DB error creating exemplar")
        return jsonify({"error": "internal database error"}), 500
    finally:
        db.close()


@catalog_bp.route("/books/<int:book_id>/exemplars/", methods=["POST"])
def create_exemplar_for_book(book_id):
    body = request.json or {}
    body["book_id"] = book_id
    return create_exemplar()


@catalog_bp.route("/exemplars/", methods=["GET"])
def list_exemplars():
    get_current_user()

    q = request.args.get("q")
    available = request.args.get("available")
    db = SessionLocal()
    try:
        qset = db.query(Exemplar)
        if q:
            qlike = f"%{q}%"
            qset = qset.join(Exemplar.book).filter(
                (Exemplar.barcode.ilike(qlike))
                | (Exemplar.book.has(Book.title.ilike(qlike)))
            )
        if available is not None:
            val = available.lower() in ("1", "true", "yes")
            qset = qset.filter(Exemplar.available == val)
        results = [e.to_dict() for e in qset.all()]
        return jsonify(results)
    finally:
        db.close()


@catalog_bp.route("/exemplars/<int:ex_id>", methods=["GET"])
def get_exemplar(ex_id):
    get_current_user()

    db = SessionLocal()
    try:
        e = db.query(Exemplar).filter(Exemplar.id == ex_id).first()
        if not e:
            return jsonify({"error": "Exemplar not found"}), 404
        return jsonify(e.to_dict())
    finally:
        db.close()


@catalog_bp.route("/exemplars/<int:ex_id>/borrow", methods=["POST"])
def borrow_exemplar(ex_id):
    user = get_current_user()

    if user["role"] not in ("student", "staff"):
        return jsonify({"error": "forbidden"}), 403

    db = SessionLocal()
    try:
        e = (
            db.query(Exemplar)
            .filter(Exemplar.id == ex_id)
            .with_for_update()
            .first()
        )
        if not e:
            return jsonify({"error": "Exemplar not found"}), 404
        if not e.available:
            return jsonify({"error": "Exemplar not available"}), 409
        e.available = False
        db.add(e)
        db.commit()
        db.refresh(e)
        return jsonify(
            {"message": "borrowed", "exemplar": e.to_dict()}
        ), 200
    except SQLAlchemyError:
        db.rollback()
        current_app.logger.exception("DB error borrowing exemplar")
        return jsonify({"error": "internal database error"}), 500
    finally:
        db.close()


@catalog_bp.route("/exemplars/<int:ex_id>/return", methods=["POST"])
def return_exemplar(ex_id):
    user = get_current_user()

    if user["role"] not in ("student", "staff"):
        return jsonify({"error": "forbidden"}), 403

    db = SessionLocal()
    try:
        e = (
            db.query(Exemplar)
            .filter(Exemplar.id == ex_id)
            .with_for_update()
            .first()
        )
        if not e:
            return jsonify({"error": "Exemplar not found"}), 404
        e.available = True
        db.add(e)
        db.commit()
        db.refresh(e)

        notify_reservation_service_exemplar_available(ex_id)
        return jsonify(
            {"message": "returned", "exemplar": e.to_dict()}
        ), 200
    except SQLAlchemyError:
        db.rollback()
        current_app.logger.exception("DB error returning exemplar")
        return jsonify({"error": "internal database error"}), 500
    finally:
        db.close()


@catalog_bp.route("/exemplars/<int:ex_id>", methods=["PATCH"])
def update_exemplar(ex_id):
    user = get_current_user()

    if user["role"] != "staff":
        return jsonify({"error": "only staff can update exemplars"}), 403

    body = request.json or {}
    db = SessionLocal()
    try:
        e = db.query(Exemplar).filter(Exemplar.id == ex_id).first()
        if not e:
            return jsonify({"error": "Exemplar not found"}), 404
        for field in ("barcode", "available", "location", "condition"):
            if field in body:
                setattr(e, field, body[field])
        db.add(e)
        db.commit()
        db.refresh(e)
        return jsonify(e.to_dict())
    except SQLAlchemyError:
        db.rollback()
        current_app.logger.exception("DB error updating exemplar")
        return jsonify({"error": "internal database error"}), 500
    finally:
        db.close()


@catalog_bp.route("/exemplars/<int:ex_id>", methods=["DELETE"])
def delete_exemplar(ex_id):
    user = get_current_user()

    if user["role"] != "staff":
        return jsonify({"error": "only staff can delete exemplars"}), 403

    db = SessionLocal()
    try:
        e = db.query(Exemplar).filter(Exemplar.id == ex_id).first()
        if not e:
            return jsonify({"error": "Exemplar not found"}), 404
        db.delete(e)
        db.commit()
        return jsonify({"message": "Exemplar deleted"}), 200
    except SQLAlchemyError:
        db.rollback()
        current_app.logger.exception("DB error deleting exemplar")
        return jsonify({"error": "internal database error"}), 500
    finally:
        db.close()
