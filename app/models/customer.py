from __future__ import annotations

from datetime import datetime

from ..extensions import db


class Customer(db.Model):
    __tablename__ = "customer"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    oib = db.Column(db.String(11), unique=True, nullable=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    assignments = db.relationship("Assignment", back_populates="customer", cascade="all, delete-orphan")
    billing_accounts = db.relationship("BillingAccount", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Customer id={self.id} name={self.name!r}>"
