from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from ..extensions import db


class InvoiceItem(db.Model):
    __tablename__ = "invoice_item"

    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey("bill.id"), nullable=False)
    item_type = db.Column(db.String(32), nullable=False, index=True)  # 'plan' or 'extra_cost'
    
    # For plan charges
    plan_id = db.Column(db.Integer, db.ForeignKey("plan.id"), nullable=True)
    
    # For extra costs
    description = db.Column(db.String(255), nullable=True)
    extra_cost_type = db.Column(db.String(50), nullable=True)  # 'SMS Parking', '3rd Party Expense', 'Miscellaneous'
    
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    bill = db.relationship("Bill", back_populates="invoice_items")
    plan = db.relationship("Plan", back_populates="invoice_items")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<InvoiceItem id={self.id} bill_id={self.bill_id} type={self.item_type} amount={self.amount} EUR>"
