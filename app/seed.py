from __future__ import annotations

import random
import string
from datetime import datetime
from typing import List, Tuple

from faker import Faker

from .extensions import db
from .models import Assignment, Customer, Sim, SimType, Plan, BillingAccount, Bill, InvoiceItem
from datetime import timedelta


faker = Faker("hr_HR")


def _generate_valid_oib(base: str = None) -> str:
    """Generate a valid Croatian OIB using ISO 7064, MOD 11-10 algorithm.
    
    Args:
        base: Optional 10-digit base. If None, generates random base.
    
    Returns:
        Valid 11-digit OIB string
    """
    if base is None:
        base = ''.join([str(random.randint(0, 9)) for _ in range(10)])
    elif len(base) != 10 or not base.isdigit():
        raise ValueError("Base must be exactly 10 digits")
    
    # Calculate check digit using ISO 7064, MOD 11-10
    a = 10
    for digit in base:
        a = a + int(digit)
        a = a % 10
        if a == 0:
            a = 10
        a = (a * 2) % 11
    
    check_digit = (11 - a) % 10
    return base + str(check_digit)


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
                oib=_generate_valid_oib(),
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


def _ensure_sim_types() -> None:
    """Ensure the 3 SIM types exist in the database."""
    try:
        # Check if SIM types already exist
        if db.session.query(SimType).first():
            return
        
        sim_types = [
            SimType(
                name="PRP SIM",
                description="Standard prepaid SIM card",
                price=2.85
            ),
            SimType(
                name="PRP Internet SIM",
                description="Prepaid internet-only SIM card",
                price=9.98
            ),
            SimType(
                name="POP SIM",
                description="Postpaid SIM card",
                price=0.00
            ),
        ]
        
        db.session.add_all(sim_types)
        db.session.commit()
    except Exception:
        db.session.rollback()


def _ensure_plans() -> None:
    """Ensure the 3 plans exist in the database."""
    try:
        # Check if plans already exist
        if db.session.query(Plan).first():
            return
        
        plans = [
            Plan(
                name="Velika kombinacija",
                description="Large combination plan",
                monthly_price=13.50
            ),
            Plan(
                name="Jako velika kombinacija",
                description="Very large combination plan",
                monthly_price=16.50
            ),
            Plan(
                name="Jako Jako velika kombinacija",
                description="Extra large combination plan",
                monthly_price=19.50
            ),
        ]
        
        db.session.add_all(plans)
        db.session.commit()
    except Exception:
        db.session.rollback()


def _ensure_sample_billing_data() -> None:
    """Create sample billing data for testing."""
    try:
        # Check if billing accounts already exist
        if db.session.query(BillingAccount).first():
            return
        
        # Get first customer
        customer = db.session.query(Customer).first()
        if not customer:
            return
        
        # Create a billing account
        ba = BillingAccount(
            account_number="9001242277",
            customer_id=customer.id,
            status="active"
        )
        db.session.add(ba)
        db.session.flush()
        
        # Get plans
        plans = db.session.query(Plan).all()
        if not plans:
            return
        
        # Create bills for last 3 months
        from datetime import datetime, timedelta
        
        for i in range(3):
            bill_date = datetime.utcnow() - timedelta(days=30 * i)
            bill_month = bill_date.strftime('%Y-%m')
            
            # Create bill
            bill = Bill(
                billing_account_id=ba.id,
                bill_month=bill_month,
                total_amount=0,  # Will update after adding items
                status='pending' if i < 2 else 'paid',
                issue_date=bill_date,
                due_date=bill_date + timedelta(days=15)
            )
            db.session.add(bill)
            db.session.flush()
            
            # Add plan item
            plan = random.choice(plans)
            plan_item = InvoiceItem(
                bill_id=bill.id,
                item_type='plan',
                plan_id=plan.id,
                amount=plan.monthly_price
            )
            db.session.add(plan_item)
            
            # Add some extra costs (randomly)
            total = float(plan.monthly_price)
            if random.random() > 0.5:
                extra_types = ['SMS Parking', '3rd Party Expense', 'Miscellaneous']
                extra_type = random.choice(extra_types)
                extra_amount = round(random.uniform(2, 15), 2)
                
                extra_item = InvoiceItem(
                    bill_id=bill.id,
                    item_type='extra_cost',
                    extra_cost_type=extra_type,
                    description=f"Additional charges for {extra_type.lower()}",
                    amount=extra_amount
                )
                db.session.add(extra_item)
                total += extra_amount
            
            # Update bill total
            bill.total_amount = total
        
        db.session.commit()
    except Exception:
        db.session.rollback()


def ensure_seed_data() -> None:
    """Populate the database with dummy data if empty.

    Idempotent: if any customer exists, seeding is skipped.
    Safe: if tables are missing (migrations not applied), it will no-op.
    """
    try:
        # Always ensure SIM types and plans are present
        _ensure_sim_types()
        _ensure_plans()
        
        if db.session.query(Customer).first():
            # If customers exist, just ensure billing data
            _ensure_sample_billing_data()
            return

        # Create 1000 customers, 1000 SIMs, and 1000 assignments (1:1 mapping)
        # Use batching to avoid memory/timeout issues
        batch_size = 100
        all_customers = []
        all_sims = []
        
        for i in range(0, 1000, batch_size):
            customers = _make_customers(batch_size)
            sims = _make_sims(batch_size)
            
            db.session.add_all(customers)
            db.session.add_all(sims)
            db.session.flush()  # Get IDs without committing
            
            # Create assignments for this batch
            assignments = _make_assignments(customers, sims)
            db.session.add_all(assignments)
            db.session.commit()
            
            all_customers.extend(customers)
            all_sims.extend(sims)
        
        # Create sample billing data
        _ensure_sample_billing_data()
    except Exception as e:
        db.session.rollback()
        print(f"Seeding error: {e}")
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
            # Delete in correct order to respect foreign key constraints
            db.session.query(InvoiceItem).delete()
            db.session.query(Bill).delete()
            db.session.query(BillingAccount).delete()
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
