"""API endpoints for chatbot and external integrations."""
import os
from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload

from .extensions import db
from .models import Assignment, Customer, Sim

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


@api_bp.route("/webhook", methods=["GET", "POST"])
def webhook():
    """Webhook endpoint for chatbot verification and message handling.
    
    GET: Webhook verification (challenge-response)
    POST: Incoming chatbot messages/events
    """
    if request.method == "GET":
        # Webhook verification for platforms like Facebook, WhatsApp, etc.
        verify_token = os.getenv("WEBHOOK_VERIFY_TOKEN", "test123")
        
        # Try different parameter formats
        # Format 1: hub.mode, hub.verify_token, hub.challenge (Facebook/Meta)
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        # Format 2: mode, verify_token, challenge (generic)
        if not mode:
            mode = request.args.get("mode")
        if not token:
            token = request.args.get("verify_token") or request.args.get("token")
        if not challenge:
            challenge = request.args.get("challenge")
        
        # Log for debugging (remove in production)
        print(f"Webhook verification attempt: mode={mode}, token_match={token == verify_token}, challenge={challenge}")
        
        # Verify token and mode
        if mode == "subscribe" and token == verify_token:
            # Respond with the challenge token
            return challenge, 200
        else:
            # Token mismatch or invalid mode
            return jsonify({
                "error": "Verification failed",
                "received_token": token,
                "expected_token": verify_token,
                "mode": mode
            }), 403
    
    elif request.method == "POST":
        # Handle incoming webhook events (messages, etc.)
        # You can process chatbot messages here
        data = request.get_json()
        
        # Log or process the incoming data
        # For now, just acknowledge receipt
        return jsonify({"status": "received"}), 200


@api_bp.route("/customers/<int:customer_id>/sims", methods=["GET"])
def get_customer_sims(customer_id: int):
    """Get all SIM cards assigned to a specific customer.
    
    Query params:
        - status: filter by SIM status (e.g., 'active', 'inactive')
        - carrier: filter by carrier name
    
    Returns:
        JSON with customer info and list of assigned SIMs with assignment details.
    """
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    
    # Build query with eager loading to avoid N+1
    query = (
        db.session.query(Sim, Assignment)
        .join(Assignment, Sim.id == Assignment.sim_id)
        .filter(Assignment.customer_id == customer_id)
    )
    
    # Optional filters from query params
    status_filter = request.args.get("status")
    if status_filter:
        query = query.filter(Sim.status == status_filter)
    
    carrier_filter = request.args.get("carrier")
    if carrier_filter:
        query = query.filter(Sim.carrier.ilike(f"%{carrier_filter}%"))
    
    results = query.all()
    
    sims_data = []
    for sim, assignment in results:
        sims_data.append({
            "id": sim.id,
            "iccid": sim.iccid,
            "msisdn": sim.msisdn,
            "carrier": sim.carrier,
            "status": sim.status,
            "created_at": sim.created_at.isoformat() if sim.created_at else None,
            "assignment": {
                "id": assignment.id,
                "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None,
                "note": assignment.note,
            }
        })
    
    return jsonify({
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
        },
        "sims": sims_data,
        "total": len(sims_data),
    }), 200


@api_bp.route("/customers/<identifier>/sims", methods=["GET"])
def get_customer_sims_by_identifier(identifier: str):
    """Get SIMs by customer email or name (for chatbot convenience).
    
    Tries to match by email first, then falls back to name (case-insensitive).
    """
    # Try email first (exact match)
    customer = db.session.query(Customer).filter(Customer.email == identifier).first()
    
    # Fall back to name (case-insensitive partial match)
    if not customer:
        customer = db.session.query(Customer).filter(Customer.name.ilike(f"%{identifier}%")).first()
    
    if not customer:
        return jsonify({"error": f"Customer not found with identifier: {identifier}"}), 404
    
    # Redirect to ID-based endpoint logic
    return get_customer_sims(customer.id)


@api_bp.route("/sims", methods=["GET"])
def list_sims():
    """List all SIMs with optional filters.
    
    Query params:
        - status: filter by status
        - carrier: filter by carrier (partial match)
        - unassigned: if 'true', only show unassigned SIMs
        - limit: max results (default 100)
        - offset: pagination offset (default 0)
    """
    query = db.session.query(Sim)
    
    # Filters
    if status := request.args.get("status"):
        query = query.filter(Sim.status == status)
    
    if carrier := request.args.get("carrier"):
        query = query.filter(Sim.carrier.ilike(f"%{carrier}%"))
    
    if request.args.get("unassigned", "").lower() == "true":
        # SIMs with no assignments
        assigned_sim_ids = db.session.query(Assignment.sim_id).distinct()
        query = query.filter(~Sim.id.in_(assigned_sim_ids))
    
    # Pagination
    limit = min(int(request.args.get("limit", 100)), 1000)
    offset = int(request.args.get("offset", 0))
    
    total = query.count()
    sims = query.limit(limit).offset(offset).all()
    
    sims_data = [
        {
            "id": sim.id,
            "iccid": sim.iccid,
            "msisdn": sim.msisdn,
            "carrier": sim.carrier,
            "status": sim.status,
            "created_at": sim.created_at.isoformat() if sim.created_at else None,
        }
        for sim in sims
    ]
    
    return jsonify({
        "sims": sims_data,
        "total": total,
        "limit": limit,
        "offset": offset,
    }), 200


@api_bp.route("/customers", methods=["GET"])
def list_customers():
    """List all customers with optional search.
    
    Query params:
        - search: search by name or email (partial match)
        - limit: max results (default 100)
        - offset: pagination offset (default 0)
    """
    query = db.session.query(Customer)
    
    if search := request.args.get("search"):
        query = query.filter(
            db.or_(
                Customer.name.ilike(f"%{search}%"),
                Customer.email.ilike(f"%{search}%"),
            )
        )
    
    limit = min(int(request.args.get("limit", 100)), 1000)
    offset = int(request.args.get("offset", 0))
    
    total = query.count()
    customers = query.limit(limit).offset(offset).all()
    
    customers_data = [
        {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "created_at": customer.created_at.isoformat() if customer.created_at else None,
        }
        for customer in customers
    ]
    
    return jsonify({
        "customers": customers_data,
        "total": total,
        "limit": limit,
        "offset": offset,
    }), 200


@api_bp.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad request", "message": str(e)}), 400


@api_bp.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@api_bp.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return jsonify({"error": "Internal server error"}), 500
