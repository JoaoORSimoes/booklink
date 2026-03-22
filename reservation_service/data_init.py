# reservation_service/data_init.py
import os
import time
import requests
from db import SessionLocal
from sqlalchemy.exc import SQLAlchemyError

from model import Reservation, ReservationStatus, ReservationItem, ItemStatus

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user_service:6000")
CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://catalog_service:7001")
STANDALONE = os.getenv("STANDALONE_MODE", "false").lower() == "true"

def _fetch_users():
    try:
        r = requests.get(f"{USER_SERVICE_URL}/users/", timeout=3)
        if r.status_code == 200:
            return [u["id"] for u in r.json()]
    except requests.RequestException:
        return None

def _fetch_exemplars():
    try:
        r = requests.get(f"{CATALOG_SERVICE_URL}/catalog/exemplars/?available=true", timeout=3)
        if r.status_code == 200:
            return [e["id"] for e in r.json()]
    except requests.RequestException:
        return None

def seed_data():
    db = SessionLocal()
    try:
        exists = db.query(Reservation).first()
        if exists:
            print("reservation_service: reservations already exist, skipping seed.")
            return

        # In standalone mode we just create dummy local user_ids/exemplar_ids
        if STANDALONE:
            user_ids = list(range(1, 21))
            exemplar_ids = list(range(1, 21))
        else:
            # tries to obtain exemplars and users from the respective services. If they are not available, wait
            user_ids = _fetch_users()
            exemplar_ids = _fetch_exemplars()
            if user_ids is None or exemplar_ids is None:
                print("reservation_service: user_service or catalog_service not ready; skipping reservation seeding.")
                return

        #creates up to 20 reservations (each with 1 item) using index matching
        count = min(20, len(user_ids), len(exemplar_ids))
        for i in range(count):
            user_id = user_ids[i]
            exemplar_id = exemplar_ids[i]
            res = Reservation(user_id=user_id, status=ReservationStatus.ACTIVE)
            db.add(res)
            db.flush()
            ri = ReservationItem(reservation_id=res.id, exemplar_id=exemplar_id, position=1, status=ItemStatus.PENDING)
            db.add(ri)

        db.commit()
        print(f"reservation_service: seeded {count} reservations (1 item each).")
    except SQLAlchemyError as e:
        db.rollback()
        print("reservation_service: error seeding reservations:", e)
    finally:
        db.close()
