from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from ..extensions import db


class Plan(db.Model):
    __tablename__ = "plan"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)
    monthly_price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationship to invoice items
    invoice_items = db.relationship("InvoiceItem", back_populates="plan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Plan id={self.id} name={self.name!r} price={self.monthly_price} EUR>"
