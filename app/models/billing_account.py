from __future__ import annotations

from datetime import datetime

from ..extensions import db


class BillingAccount(db.Model):
    __tablename__ = "billing_account"

    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    status = db.Column(db.String(32), nullable=True, default="active")  # active, suspended, closed
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    customer = db.relationship("Customer", back_populates="billing_accounts")
    bills = db.relationship("Bill", back_populates="billing_account", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<BillingAccount id={self.id} number={self.account_number!r} customer_id={self.customer_id}>"
