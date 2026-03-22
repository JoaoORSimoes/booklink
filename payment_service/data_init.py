# payment_service/data_init.py
from db import SessionLocal
from sqlalchemy.exc import SQLAlchemyError
import uuid

from model import PaymentStatus, PaymentModel


def seed_data():
    db = SessionLocal()
    try:
        exists = db.query(PaymentModel).first()
        if exists:
            print("payment_service: payments already exist, skipping seed.")
            return

        for i in range(1, 21):
            p = PaymentModel(
                reservation_id=1000 + i,
                user_id=i,
                amount=round(1.5 + i * 0.5, 2),
                method="card",
            )
            p.status = PaymentStatus.COMPLETED
            p.txn_id = f"SIM-{uuid.uuid4().hex[:8]}"
            db.add(p)

        db.commit()
        print("payment_service: seeded 20 payments.")
    except SQLAlchemyError as e:
        db.rollback()
        print("payment_service: error seeding payments:", e)
    finally:
        db.close()
