from __future__ import annotations

import random
import string
from datetime import datetime
from typing import List, Tuple

from faker import Faker

from .extensions import db
from .models import Assignment, Customer, Sim


faker = Faker("hr_HR")


def _luhn_checksum(number: str) -> int:
    total = 0
    reverse_digits = list(map(int, number[::-1]))
    for i, d in enumerate(reverse_digits, start=1):
        if i % 2 == 1:
            total += d
        else:
            dd = d * 2
            if dd > 9:
                dd -= 9
            total += dd
    return (10 - (total % 10)) % 10


def _iccid_hr(mnc: str | None = None, length: int = 19) -> str:
    """Generate a Croatian-like ICCID.

    Structure (approx): 89 + 385 (HR) + MNC-ish + random + Luhn check.
    Default total length 19.
    """
    # Common Croatian operator codes (illustrative): HT=01, A1=10, Telemach=02
    mnc = mnc or random.choice(["01", "10", "02"])
    base = "89" + "385" + mnc
    # leave one digit for check
    payload_len = length - 1 - len(base)
    payload = "".join(random.choices(string.digits, k=max(0, payload_len)))
    partial = base + payload
    check = _luhn_checksum(partial)
    return partial + str(check)


def _msisdn_hr() -> str:
    """Generate a Croatian MSISDN in E.164 format, e.g., +3859XXXXXXXX.

    Uses common mobile prefixes: 91, 92, 95, 97, 98, 99.
    """
    prefix = random.choice(["91", "92", "95", "97", "98", "99"])  # illustrative
    rest = "".join(random.choices(string.digits, k=7))
    return "+385" + prefix + rest


def _make_customers(n: int = 5) -> List[Customer]:
    customers: List[Customer] = []
    for _ in range(n):
        customers.append(
            Customer(
                name=faker.name(),
                email=faker.free_email(),
                created_at=datetime.utcnow(),
            )
        )
    return customers


def _make_sims(n: int = 10) -> List[Sim]:
    sims: List[Sim] = []
    carriers = [
        "Hrvatski Telekom",
        "A1 Hrvatska",
        "Telemach Hrvatska",
    ]
    statuses = ["active", "inactive", "provisioning"]
    for _ in range(n):
        iccid = _iccid_hr()
        msisdn = _msisdn_hr()
        sim = Sim(
            iccid=iccid,
            carrier=random.choice(carriers),
            status=random.choice(statuses),
            created_at=datetime.utcnow(),
        )
        # Assign MSISDN if model defines the column (migration may not be applied yet)
        if hasattr(Sim, "msisdn"):
            try:
                setattr(sim, "msisdn", msisdn)
            except Exception:
                pass
        sims.append(sim)
    return sims


def _make_assignments(customers: List[Customer], sims: List[Sim]) -> List[Assignment]:
    assignments: List[Assignment] = []
    pairs = zip(customers, sims)
    for c, s in pairs:
        assignments.append(
            Assignment(
                customer=c,
                sim=s,
                assigned_at=datetime.utcnow(),
                note="Auto-seeded",
            )
        )
    return assignments


def ensure_seed_data() -> None:
    """Populate the database with dummy data if empty.

    Idempotent: if any customer exists, seeding is skipped.
    Safe: if tables are missing (migrations not applied), it will no-op.
    """
    try:
        if db.session.query(Customer).first():
            return

        customers = _make_customers(5)
        sims = _make_sims(10)
        assignments = _make_assignments(customers, sims)

        db.session.add_all(customers)
        db.session.add_all(sims)
        db.session.add_all(assignments)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return


def seed_bulk(num_customers: int = 1000, num_sims: int = 1000, num_assignments: int = 1000, reset: bool = False) -> Tuple[int, int, int]:
    """Bulk-seed database with specified counts.

    - Ensures unique ICCID/MSISDN generation.
    - Optionally clears existing data first when reset=True.
    - Returns a tuple of inserted counts: (customers, sims, assignments).
    """
    inserted_c = inserted_s = inserted_a = 0
    try:
        if reset:
            db.session.query(Assignment).delete()
            db.session.query(Sim).delete()
            db.session.query(Customer).delete()
            db.session.commit()

        existing_customers = db.session.query(Customer).count()
        existing_sims = db.session.query(Sim).count()

        target_customers = max(0, num_customers - existing_customers)
        target_sims = max(0, num_sims - existing_sims)

        # Generate customers
        batch_size = 500
        while target_customers > 0:
            make = min(batch_size, target_customers)
            new_customers = _make_customers(make)
            db.session.add_all(new_customers)
            db.session.commit()
            inserted_c += len(new_customers)
            target_customers -= len(new_customers)

        # Generate sims with strong uniqueness safeguards
        iccids = set(db.session.query(Sim.iccid).distinct())
        msisdns = set(db.session.query(Sim.msisdn).filter(Sim.msisdn.isnot(None)).distinct()) if hasattr(Sim, "msisdn") else set()

        def _unique_sim_batch(k: int) -> List[Sim]:
            out: List[Sim] = []
            attempts = 0
            while len(out) < k and attempts < k * 20:
                attempts += 1
                iccid = _iccid_hr()
                if iccid in iccids:
                    continue
                msisdn_val = _msisdn_hr() if hasattr(Sim, "msisdn") else None
                if msisdn_val and msisdn_val in msisdns:
                    continue
                sim = Sim(
                    iccid=iccid,
                    carrier=random.choice(["Hrvatski Telekom", "A1 Hrvatska", "Telemach Hrvatska"]),
                    status=random.choice(["active", "inactive", "provisioning"]),
                    created_at=datetime.utcnow(),
                )
                if hasattr(Sim, "msisdn"):
                    setattr(sim, "msisdn", msisdn_val)
                iccids.add(iccid)
                if msisdn_val:
                    msisdns.add(msisdn_val)
                out.append(sim)
            return out

        while target_sims > 0:
            make = min(batch_size, target_sims)
            new_sims = _unique_sim_batch(make)
            if not new_sims:
                break
            db.session.add_all(new_sims)
            db.session.commit()
            inserted_s += len(new_sims)
            target_sims -= len(new_sims)

        # Assignments: avoid duplicates per uq_customer_sim
        # We'll create up to num_assignments unique pairs
        total_customers = db.session.query(Customer).count()
        total_sims = db.session.query(Sim).count()
        max_pairs = total_customers * total_sims
        desired = min(num_assignments, max_pairs)

        # Build ID lists to sample
        customer_ids = [c.id for c in db.session.query(Customer.id).all()]
        sim_ids = [s.id for s in db.session.query(Sim.id).all()]
        rng = random.Random()
        seen_pairs: set[Tuple[int, int]] = set(
            (a.customer_id, a.sim_id) for a in db.session.query(Assignment.customer_id, Assignment.sim_id)
        )

        to_create: List[Assignment] = []
        attempts = 0
        while len(to_create) < desired and attempts < desired * 20:
            attempts += 1
            cid = rng.choice(customer_ids)
            sid = rng.choice(sim_ids)
            pair = (cid, sid)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            to_create.append(
                Assignment(
                    customer_id=cid,
                    sim_id=sid,
                    assigned_at=datetime.utcnow(),
                    note="CLI-seeded",
                )
            )

        for i in range(0, len(to_create), batch_size):
            batch = to_create[i : i + batch_size]
            db.session.add_all(batch)
            db.session.commit()
            inserted_a += len(batch)

        return inserted_c, inserted_s, inserted_a
    except Exception:
        db.session.rollback()
        raise
