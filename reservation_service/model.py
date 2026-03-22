import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, func, Boolean
from sqlalchemy.orm import relationship
from db import Base

class ReservationStatus(enum.Enum):
    ACTIVE = "ACTIVE"          # in line, waiting for availability
    NOTIFIED = "NOTIFIED"      # uuser notified that it's available (next in line)
    FULFILLED = "FULFILLED"    # transformed into loan / withdrawn
    CANCELLED = "CANCELLED"    # canceled

class ItemStatus(enum.Enum):
    PENDING = "PENDING"        # wating in line
    NOTIFIED = "NOTIFIED"      # notified that it's available (next in line)
    FULFILLED = "FULFILLED"    # withdrawn / transformed into loan
    CANCELLED = "CANCELLED"

class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    items = relationship("ReservationItem", back_populates="reservation", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "items": [i.to_dict() for i in self.items]
        }

class ReservationItem(Base):
    __tablename__ = "reservation_items"
    id = Column(Integer, primary_key=True, index=True)
    reservation_id = Column(Integer, ForeignKey("reservations.id"), nullable=False)
    exemplar_id = Column(Integer, index=True, nullable=False)
    position = Column(Integer, nullable=False)  # posição na fila para esse exemplar
    status = Column(Enum(ItemStatus), default=ItemStatus.PENDING, nullable=False)
    notified_at = Column(DateTime(timezone=True), nullable=True)
    fulfilled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled = Column(Boolean, default=False)

    reservation = relationship("Reservation", back_populates="items")

    def to_dict(self):
        return {
            "id": self.id,
            "reservation_id": self.reservation_id,
            "exemplar_id": self.exemplar_id,
            "position": self.position,
            "status": self.status.value if self.status else None,
            "notified_at": self.notified_at.isoformat() if self.notified_at else None,
            "fulfilled_at": self.fulfilled_at.isoformat() if self.fulfilled_at else None,
            "cancelled": bool(self.cancelled)
        }
