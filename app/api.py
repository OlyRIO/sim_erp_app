"""API endpoints for chatbot and external integrations."""
import os
from datetime import datetime
from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload

from .extensions import db
from .models import Assignment, Customer, Sim
from .chatbot_service import handle_user_message

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


@api_bp.route("/webhook", methods=["GET", "POST"])
def webhook():
    """Webhook endpoint for chatbot verification and message handling.
    
    GET: Webhook verification (challenge-response)
    POST: Incoming chatbot messages/events
    """
    if request.method == "GET":
        # Chatbot.com verification format:
        # - Sends ?token=YOUR_TOKEN&challenge=RANDOM_STRING
        # - Must verify token matches, then return challenge
        
        verify_token = os.getenv("WEBHOOK_VERIFY_TOKEN", "test123")
        token = request.args.get("token")
        challenge = request.args.get("challenge")
        
        # Check if verification token is correct
        if token != verify_token:
            return "", 401
        
        # Return challenge to Chatbot.com
        return challenge, 200, {"Content-Type": "text/plain"}
    
    elif request.method == "POST":
        # Handle incoming webhook events from Chatbot.com
        data = request.get_json()
        
        # Log incoming data for debugging
        print(f"Webhook POST received: {data}")
        
        # Acknowledge receipt
        return jsonify({"status": "ok"}), 200


@api_bp.route("/my/sims", methods=["GET"])
def get_my_sims():
    """Get SIM cards for the authenticated user (via header).
    
    Headers:
        - X-User-Email: Customer email address
        - X-User-ID: Customer ID (alternative to email)
    
    Query params (optional):
        - status: filter by SIM status
        - carrier: filter by carrier name
    
    Returns:
        JSON with customer info and list of assigned SIMs.
    """
    # Try to get user identifier from headers
    user_email = request.headers.get("X-User-Email")
    user_id = request.headers.get("X-User-ID")
    
    if not user_email and not user_id:
        return jsonify({
            "error": "Missing user identifier",
            "message": "Provide X-User-Email or X-User-ID header"
        }), 400
    
    # Find customer by email or ID
    if user_email:
        customer = db.session.query(Customer).filter(Customer.email == user_email).first()
    else:
        customer = db.session.get(Customer, int(user_id))
    
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    
    # Build query with filters
    query = (
        db.session.query(Sim, Assignment)
        .join(Assignment, Sim.id == Assignment.sim_id)
        .filter(Assignment.customer_id == customer.id)
    )
    
    # Optional filters
    if status := request.args.get("status"):
        query = query.filter(Sim.status == status)
    
    if carrier := request.args.get("carrier"):
        query = query.filter(Sim.carrier.ilike(f"%{carrier}%"))
    
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


@api_bp.route("/chatbot/message", methods=["POST"])
def chatbot_message():
    """Handle chatbot messages.
    
    Request JSON:
        {
            "user_id": "unique_user_identifier",
            "message": "user's message text"
        }
    
    Response JSON:
        {
            "message": "bot's response",
            "timestamp": "ISO timestamp"
        }
    """
    data = request.get_json()
    
    if not data or 'user_id' not in data or 'message' not in data:
        return jsonify({
            "error": "Missing required fields",
            "message": "Request must include 'user_id' and 'message'"
        }), 400
    
    user_id = str(data['user_id'])
    user_message = str(data['message'])
    
    try:
        response = handle_user_message(user_id, user_message)
        
        # Return full response including state
        return jsonify({
            "message": response.get('message', ''),
            "state": response.get('state', 'initial'),
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Processing error",
            "message": str(e)
        }), 500
