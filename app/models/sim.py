from __future__ import annotations

from datetime import datetime

from ..extensions import db


class Sim(db.Model):
    __tablename__ = "sim"

    id = db.Column(db.Integer, primary_key=True)
    iccid = db.Column(db.String(32), unique=True, nullable=False, index=True)
    msisdn = db.Column(db.String(16), unique=True, nullable=True, index=True)
    carrier = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(32), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    assignments = db.relationship("Assignment", back_populates="sim", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Sim id={self.id} iccid={self.iccid!r}>"
