from flask import Blueprint, render_template, jsonify, request
from sqlalchemy import func, or_
from .extensions import db
from .models import Sim

core_bp = Blueprint("core", __name__)


@core_bp.route("/")
def dashboard():
    return render_template("dashboard.html", page_title="Dashboard Overview")


@core_bp.route("/sims")
def sim_inventory():
    return render_template("sims.html", page_title="SIM Inventory")


@core_bp.route("/assignments")
def assignments():
    return render_template("assignments.html", page_title="Assignments Board")


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
