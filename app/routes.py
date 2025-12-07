import random

from flask import Blueprint, render_template, jsonify, request
from sqlalchemy import func, or_
from .extensions import db
from .models import Assignment, BillingAccount, Customer, Sim

core_bp = Blueprint("core", __name__)


@core_bp.route("/")
def dashboard():
    return render_template("dashboard.html", page_title="Dashboard Overview")


@core_bp.route("/sims")
def sim_inventory():
    return render_template("sims.html", page_title="SIM Inventory")


@core_bp.route("/assignments")
def assignments():
    return render_template("assignments.html", page_title="SIM & Customer Updates")


@core_bp.route("/customers")
def customers():
    return render_template("customers.html", page_title="Customer Directory")


@core_bp.route("/api/sim-status-distribution")
def sim_status_distribution():
    """API endpoint returning SIM status distribution for D3.js visualization."""
    results = db.session.query(
        Sim.status,
        func.count(Sim.id).label('count')
    ).group_by(Sim.status).all()
    
    data = [{"status": status or "unknown", "count": count} for status, count in results]
    return jsonify(data)


@core_bp.route("/api/sim-carrier-distribution")
def sim_carrier_distribution():
    """API endpoint returning SIM carrier distribution for D3.js visualization."""
    results = db.session.query(
        Sim.carrier,
        func.count(Sim.id).label('count')
    ).group_by(Sim.carrier).order_by(func.count(Sim.id).desc()).all()
    
    data = [{"carrier": carrier or "Unknown", "count": count} for carrier, count in results]
    return jsonify(data)


@core_bp.route("/api/sims")
def get_sims():
    """API endpoint returning paginated and filtered SIM data."""
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status_filter = request.args.get('status', '')
    iccid_filter = request.args.get('iccid', '')
    msisdn_filter = request.args.get('msisdn', '')
    
    # Build query
    query = Sim.query
    
    # Apply filters
    if status_filter:
        query = query.filter(Sim.status == status_filter)
    
    if iccid_filter:
        query = query.filter(Sim.iccid.ilike(f'%{iccid_filter}%'))
    
    if msisdn_filter:
        query = query.filter(Sim.msisdn.ilike(f'%{msisdn_filter}%'))
    
    # Order by created_at descending (newest first)
    query = query.order_by(Sim.created_at.desc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Format results
    sims = [{
        'id': sim.id,
        'iccid': sim.iccid,
        'msisdn': sim.msisdn or 'N/A',
        'status': sim.status or 'unknown',
        'carrier': sim.carrier or 'N/A',
        'created_at': sim.created_at.strftime('%Y-%m-%d %H:%M')
    } for sim in pagination.items]
    
    return jsonify({
        'sims': sims,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@core_bp.route("/api/customers")
def get_customers():
    """API endpoint returning paginated and filtered Customer data."""
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    oib_filter = request.args.get('oib', '')
    name_filter = request.args.get('name', '')
    msisdn_filter = request.args.get('msisdn', '')
    
    # Build query
    query = Customer.query
    
    # Apply filters
    if oib_filter:
        query = query.filter(Customer.oib.ilike(f'%{oib_filter}%'))
    
    if name_filter:
        query = query.filter(Customer.name.ilike(f'%{name_filter}%'))
    
    if msisdn_filter:
        # Search by MSISDN through assignments and sims
        query = query.join(Assignment).join(Sim).filter(
            Sim.msisdn.ilike(f'%{msisdn_filter}%')
        ).distinct()
    
    # Order by created_at descending (newest first)
    query = query.order_by(Customer.created_at.desc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Collect customer IDs on this page
    page_customers = pagination.items
    customer_ids = [c.id for c in page_customers]

    # Map existing billing accounts for these customers
    ba_rows = db.session.query(BillingAccount.customer_id, BillingAccount.account_number).filter(
        BillingAccount.customer_id.in_(customer_ids)
    ).all()
    ba_map = {cid: acct for cid, acct in ba_rows}

    # Backfill missing billing accounts (helps already-deployed DBs without BAs)
    missing_ids = [cid for cid in customer_ids if cid not in ba_map]
    if missing_ids:
        try:
            existing_numbers = set(num for (num,) in db.session.query(BillingAccount.account_number).all())
            new_accounts = []
            for cid in missing_ids:
                ba_number = f"900{random.randint(1000000, 9999999)}"
                while ba_number in existing_numbers:
                    ba_number = f"900{random.randint(1000000, 9999999)}"
                existing_numbers.add(ba_number)
                new_accounts.append(BillingAccount(
                    account_number=ba_number,
                    customer_id=cid,
                    status="active"
                ))
            if new_accounts:
                db.session.add_all(new_accounts)
                db.session.commit()
                for acct in new_accounts:
                    ba_map[acct.customer_id] = acct.account_number
        except Exception:
            db.session.rollback()

    # Format results
    customers = [{
        'id': customer.id,
        'name': customer.name,
        'email': customer.email or 'N/A',
        'oib': customer.oib or 'N/A',
        'billing_account': ba_map.get(customer.id, 'N/A'),
        'sim_count': len(customer.assignments),
        'created_at': customer.created_at.strftime('%Y-%m-%d %H:%M')
    } for customer in page_customers]
    
    return jsonify({
        'customers': customers,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@core_bp.route("/api/search/sims")
def search_sims():
    """Search SIMs by ICCID or MSISDN for editing."""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'error': 'Query parameter required'}), 400
    
    results = Sim.query.filter(
        or_(Sim.iccid.ilike(f'%{query}%'), Sim.msisdn.ilike(f'%{query}%'))
    ).limit(10).all()
    
    data = [{
        'id': sim.id,
        'iccid': sim.iccid,
        'msisdn': sim.msisdn or 'N/A',
        'status': sim.status or 'unknown',
        'carrier': sim.carrier or 'N/A'
    } for sim in results]
    
    return jsonify(data)


@core_bp.route("/api/search/customers")
def search_customers():
    """Search customers by name or OIB for editing."""
    from .models import Customer
    
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'error': 'Query parameter required'}), 400
    
    results = Customer.query.filter(
        or_(Customer.name.ilike(f'%{query}%'), Customer.oib.ilike(f'%{query}%'))
    ).limit(10).all()
    
    data = [{
        'id': customer.id,
        'name': customer.name,
        'email': customer.email or '',
        'oib': customer.oib or 'N/A'
    } for customer in results]
    
    return jsonify(data)


@core_bp.route("/api/sims/<int:sim_id>", methods=['PUT'])
def update_sim(sim_id):
    """Update SIM status."""
    sim = db.session.get(Sim, sim_id)
    
    if not sim:
        return jsonify({'error': 'SIM not found'}), 404
    
    data = request.get_json()
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({'error': 'Status is required'}), 400
    
    valid_statuses = ['active', 'inactive', 'suspended', 'available', 'provisioning']
    if new_status not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
    
    old_status = sim.status
    sim.status = new_status
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'SIM status updated from {old_status} to {new_status}',
            'sim': {
                'id': sim.id,
                'iccid': sim.iccid,
                'status': sim.status
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@core_bp.route("/api/customers/<int:customer_id>", methods=['PUT'])
def update_customer(customer_id):
    """Update customer information."""
    from .models import Customer
    
    customer = db.session.get(Customer, customer_id)
    
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    
    data = request.get_json()
    
    # Update fields if provided
    if 'name' in data:
        if not data['name'].strip():
            return jsonify({'error': 'Name cannot be empty'}), 400
        customer.name = data['name'].strip()
    
    if 'email' in data:
        email = data['email'].strip()
        if email:
            # Check for duplicate email
            existing = Customer.query.filter(
                Customer.email == email,
                Customer.id != customer_id
            ).first()
            if existing:
                return jsonify({'error': 'Email already in use'}), 400
        customer.email = email if email else None
    
    if 'oib' in data:
        oib = data['oib'].strip()
        if oib:
            # Check for duplicate OIB
            existing = Customer.query.filter(
                Customer.oib == oib,
                Customer.id != customer_id
            ).first()
            if existing:
                return jsonify({'error': 'OIB already in use'}), 400
        customer.oib = oib if oib else None
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Customer information updated successfully',
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'email': customer.email or '',
                'oib': customer.oib or ''
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
