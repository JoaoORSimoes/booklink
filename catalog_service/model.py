from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from db import Base

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    authors = Column(String(255), nullable=True)
    isbn = Column(String(32), unique=True, nullable=True)
    publisher = Column(String(255), nullable=True)
    year = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    exemplars = relationship("Exemplar", back_populates="book", cascade="all, delete-orphan")

    def to_dict(self, include_exemplars: bool = False):
        base = {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "isbn": self.isbn,
            "publisher": self.publisher,
            "year": self.year,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        if include_exemplars:
            base["exemplars"] = [e.to_dict() for e in self.exemplars]
        return base

class Exemplar(Base):
    __tablename__ = "exemplars"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    barcode = Column(String(100), unique=True, nullable=True)   # identificador físico
    available = Column(Boolean, default=True, nullable=False)
    location = Column(String(100), nullable=True)
    condition = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    book = relationship("Book", back_populates="exemplars")

    def to_dict(self):
        return {
            "id": self.id,
            "book_id": self.book_id,
            "barcode": self.barcode,
            "available": bool(self.available),
            "location": self.location,
            "condition": self.condition,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
