from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from ..extensions import db


class Bill(db.Model):
    __tablename__ = "bill"

    id = db.Column(db.Integer, primary_key=True)
    billing_account_id = db.Column(db.Integer, db.ForeignKey("billing_account.id"), nullable=False)
    bill_month = db.Column(db.String(7), nullable=False, index=True)  # Format: YYYY-MM
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    status = db.Column(db.String(32), nullable=True, default="pending")  # pending, paid, overdue
    issue_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    billing_account = db.relationship("BillingAccount", back_populates="bills")
    invoice_items = db.relationship("InvoiceItem", back_populates="bill", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Bill id={self.id} BA={self.billing_account_id} month={self.bill_month} total={self.total_amount}€>"
