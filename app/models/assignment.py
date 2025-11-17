from __future__ import annotations

from datetime import datetime

from ..extensions import db


class Assignment(db.Model):
    __tablename__ = "assignment"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False, index=True)
    sim_id = db.Column(db.Integer, db.ForeignKey("sim.id"), nullable=False, index=True)
    assigned_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    note = db.Column(db.String(255), nullable=True)

    customer = db.relationship("Customer", back_populates="assignments")
    sim = db.relationship("Sim", back_populates="assignments")

    __table_args__ = (
        db.UniqueConstraint("customer_id", "sim_id", name="uq_customer_sim"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Assignment id={self.id} customer_id={self.customer_id} sim_id={self.sim_id}>"
