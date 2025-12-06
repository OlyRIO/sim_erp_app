from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from ..extensions import db


class SimType(db.Model):
    __tablename__ = "sim_type"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)  # Price in euros
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationship with SIM cards
    sims = db.relationship("Sim", back_populates="sim_type")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SimType id={self.id} name={self.name!r} price={self.price} EUR>"
