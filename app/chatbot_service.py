"""Chatbot service for handling user conversations."""
from typing import Dict, Any, Optional
from datetime import datetime
from flask import session
from .extensions import db
from .models import Customer, Sim, Assignment, SimType, BillingAccount, Bill, InvoiceItem


OPTIONS = {
    1: "📱 Tell me which type of SIM cards I can get in your company",
    2: "🔍 Check Service Status",
    3: "📚 Get Help & Documentation",
    4: "✏️ Update Database Entry",
    5: "👤 Retrieve User Information",
    6: "📄 Give me my open bills",
    7: "📋 Give me my last open bill"
}

CONSTANT_INFO = {
    2: """**Service Status:**
✅ All Systems Operational
• Database: Online
• API Services: Running
• Response Time: <50ms
• Uptime: 99.9%""",
    
    3: """**Help & Documentation:**
📖 User Guide: Available in dashboard
📧 Support Email: support@ispsim.com
🔗 API Docs: /api/v1/docs
💬 Live Chat: You're using it now!
⏰ Support Hours: 24/7"""
}


def get_or_create_session() -> Dict[str, Any]:
    """Get existing session or create new one using Flask session."""
    if 'chatbot_state' not in session:
        session['chatbot_state'] = {
            'state': 'initial',
            'selected_option': None,
            'context': {},
        }
    return session['chatbot_state']


def clear_session() -> None:
    """Clear user session."""
    if 'chatbot_state' in session:
        del session['chatbot_state']


def present_options() -> Dict[str, Any]:
    """Present the main menu options."""
    options_text = "**What can I help you with?**\n\n"
    for num, desc in OPTIONS.items():
        options_text += f"{num}. {desc}\n"
    options_text += "\nReply with a number (1-7) to select an option."
    
    return {
        'message': options_text,
        'options': list(OPTIONS.values()),
        'state': 'awaiting_option'
    }


def parse_option(message: str) -> Optional[int]:
    """Parse user input to extract option number."""
    message = message.strip()
    try:
        option = int(message)
        if 1 <= option <= 7:
            return option
    except ValueError:
        pass
    return None


def get_sim_types() -> Dict[str, Any]:
    """Fetch and display available SIM types from database."""
    try:
        sim_types = db.session.query(SimType).order_by(SimType.id).all()
        
        if not sim_types:
            return {
                'message': '❌ No SIM types available at the moment.',
                'state': 'initial',
                'reset': True
            }
        
        response = "**Available SIM Card Types:**\n\n"
        for sim_type in sim_types:
            price_str = f"€{float(sim_type.price):.2f}" if sim_type.price > 0 else "FREE"
            response += f"📱 **{sim_type.name}**\n"
            if sim_type.description:
                response += f"   {sim_type.description}\n"
            response += f"   Price: {price_str}\n\n"
        
        return {
            'message': response.strip(),
            'state': 'initial',
            'reset': True
        }
    except Exception as e:
        return {
            'message': f'❌ Error fetching SIM types: {str(e)}',
            'state': 'initial',
            'reset': True
        }


def handle_info_option(option: int) -> Dict[str, Any]:
    """Handle options 2-3 that display constant information."""
    return {
        'message': CONSTANT_INFO[option],
        'state': 'initial',
        'reset': True
    }


def handle_update_request() -> Dict[str, Any]:
    """Handle option 4 - request data for database update."""
    return {
        'message': """**Update Database Entry**

Please provide the following information in this format:
```
ID: [customer_id]
NAME: [new_name]
EMAIL: [new_email]
```

Example:
```
ID: 5
NAME: John Smith
EMAIL: john.smith@example.com
```""",
        'state': 'awaiting_update_data'
    }


def parse_update_data(message: str) -> Optional[Dict[str, str]]:
    """Parse update data from user message."""
    data = {}
    lines = message.strip().split('\n')
    
    for line in lines:
        line = line.strip().replace('```', '')
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().upper()
            value = value.strip()
            if key in ['ID', 'NAME', 'EMAIL']:
                data[key] = value
    
    # Validate required fields
    if 'ID' in data and ('NAME' in data or 'EMAIL' in data):
        return data
    return None


def process_update(message: str) -> Dict[str, Any]:
    """Process database update request."""
    data = parse_update_data(message)
    
    if not data:
        return {
            'message': '❌ Invalid format. Please provide ID and at least one field to update (NAME or EMAIL).',
            'state': 'awaiting_update_data'
        }
    
    try:
        customer_id = int(data['ID'])
        customer = db.session.get(Customer, customer_id)
        
        if not customer:
            return {
                'message': f'❌ Customer with ID {customer_id} not found.',
                'state': 'initial',
                'reset': True
            }
        
        # Update fields if provided
        updated_fields = []
        if 'NAME' in data:
            customer.name = data['NAME']
            updated_fields.append(f"Name → {data['NAME']}")
        
        if 'EMAIL' in data:
            # Check for duplicate email
            existing = db.session.query(Customer).filter(
                Customer.email == data['EMAIL'],
                Customer.id != customer_id
            ).first()
            
            if existing:
                return {
                    'message': f'❌ Email {data["EMAIL"]} is already in use by another customer.',
                    'state': 'initial',
                    'reset': True
                }
            
            customer.email = data['EMAIL']
            updated_fields.append(f"Email → {data['EMAIL']}")
        
        db.session.commit()
        
        return {
            'message': f"""✅ **Customer Updated Successfully!**

**Customer ID:** {customer_id}
**Updated Fields:**
{chr(10).join('• ' + field for field in updated_fields)}""",
            'state': 'initial',
            'reset': True
        }
        
    except ValueError:
        return {
            'message': '❌ Invalid ID format. Please provide a numeric customer ID.',
            'state': 'awaiting_update_data'
        }
    except Exception as e:
        db.session.rollback()
        return {
            'message': f'❌ Database error: {str(e)}',
            'state': 'initial',
            'reset': True
        }


def handle_fetch_request() -> Dict[str, Any]:
    """Handle option 5 - request identifier for user info fetch."""
    return {
        'message': """**Retrieve User Information**

Please provide either:
• Customer ID (e.g., `123`)
• Email address (e.g., `user@example.com`)""",
        'state': 'awaiting_identifier'
    }


def fetch_user_info(message: str) -> Dict[str, Any]:
    """Fetch and display user information."""
    identifier = message.strip()
    
    # Try to find customer by ID or email
    customer = None
    
    # Try ID first
    try:
        customer_id = int(identifier)
        customer = db.session.get(Customer, customer_id)
    except ValueError:
        # Not a number, try email
        customer = db.session.query(Customer).filter(Customer.email == identifier).first()
    
    if not customer:
        return {
            'message': f'❌ No customer found with identifier: {identifier}',
            'state': 'initial',
            'reset': True
        }
    
    # Fetch assigned SIMs
    assignments = db.session.query(Assignment, Sim).join(
        Sim, Assignment.sim_id == Sim.id
    ).filter(Assignment.customer_id == customer.id).all()
    
    # Build response
    response = f"""✅ **Customer Information**

**ID:** {customer.id}
**Name:** {customer.name}
**Email:** {customer.email or 'N/A'}
**Created:** {customer.created_at.strftime('%Y-%m-%d %H:%M')}

**Assigned SIM Cards:** {len(assignments)}
"""
    
    if assignments:
        response += "\n"
        for idx, (assignment, sim) in enumerate(assignments[:5], 1):
            response += f"\n{idx}. **{sim.iccid}** ({sim.carrier}) - {sim.status}"
            response += f"\n   Assigned: {assignment.assigned_at.strftime('%Y-%m-%d')}"
        
        if len(assignments) > 5:
            response += f"\n\n... and {len(assignments) - 5} more SIM(s)"
    
    return {
        'message': response,
        'state': 'initial',
        'reset': True
    }


def handle_open_bills_request() -> Dict[str, Any]:
    """Handle option 6 - request BA for open bills."""
    return {
        'message': """**View Open Bills**

Please provide your Billing Account number (e.g., `BA12345`)""",
        'state': 'awaiting_ba_for_bills'
    }


def handle_last_bill_request() -> Dict[str, Any]:
    """Handle option 7 - request BA for last open bill."""
    return {
        'message': """**View Last Open Bill**

Please provide your Billing Account number (e.g., `BA12345`)""",
        'state': 'awaiting_ba_for_last_bill'
    }


def fetch_open_bills(ba_number: str) -> Dict[str, Any]:
    """Fetch and display all open bills for a billing account."""
    ba_number = ba_number.strip()
    
    # Find billing account
    billing_account = db.session.query(BillingAccount).filter(
        BillingAccount.account_number == ba_number
    ).first()
    
    if not billing_account:
        return {
            'message': f'❌ No billing account found with number: {ba_number}',
            'state': 'initial',
            'reset': True
        }
    
    # Fetch open bills (pending or overdue)
    open_bills = db.session.query(Bill).filter(
        Bill.billing_account_id == billing_account.id,
        Bill.status.in_(['pending', 'overdue'])
    ).order_by(Bill.bill_month.desc()).all()
    
    if not open_bills:
        return {
            'message': f"""✅ **No Open Bills**

**Billing Account:** {ba_number}
**Customer:** {billing_account.customer.name}

You have no open bills at this time.""",
            'state': 'initial',
            'reset': True
        }
    
    # Build response
    response = f"""✅ **Open Bills**

**Billing Account:** {ba_number}
**Customer:** {billing_account.customer.name}
**Number of Open Bills:** {len(open_bills)}

"""
    
    for bill in open_bills:
        status_emoji = "⚠️" if bill.status == 'overdue' else "⏳"
        response += f"\n{status_emoji} **{bill.bill_month}**"
        response += f"\n   Amount: €{float(bill.total_amount):.2f}"
        response += f"\n   Status: {bill.status.capitalize()}"
        if bill.due_date:
            response += f"\n   Due: {bill.due_date.strftime('%Y-%m-%d')}"
        response += "\n"
    
    return {
        'message': response.strip(),
        'state': 'initial',
        'reset': True
    }


def fetch_last_open_bill(ba_number: str) -> Dict[str, Any]:
    """Fetch and display the most recent open bill for a billing account."""
    ba_number = ba_number.strip()
    
    # Find billing account
    billing_account = db.session.query(BillingAccount).filter(
        BillingAccount.account_number == ba_number
    ).first()
    
    if not billing_account:
        return {
            'message': f'❌ No billing account found with number: {ba_number}',
            'state': 'initial',
            'reset': True
        }
    
    # Fetch most recent open bill
    last_bill = db.session.query(Bill).filter(
        Bill.billing_account_id == billing_account.id,
        Bill.status.in_(['pending', 'overdue'])
    ).order_by(Bill.bill_month.desc()).first()
    
    if not last_bill:
        return {
            'message': f"""✅ **No Open Bills**

**Billing Account:** {ba_number}
**Customer:** {billing_account.customer.name}

You have no open bills at this time.""",
            'state': 'initial',
            'reset': True
        }
    
    # Fetch invoice items for this bill
    items = db.session.query(InvoiceItem).filter(
        InvoiceItem.bill_id == last_bill.id
    ).all()
    
    # Build response
    status_emoji = "⚠️" if last_bill.status == 'overdue' else "⏳"
    response = f"""✅ **Latest Open Bill**

**Billing Account:** {ba_number}
**Customer:** {billing_account.customer.name}

{status_emoji} **Bill for {last_bill.bill_month}**
**Status:** {last_bill.status.capitalize()}
**Total Amount:** €{float(last_bill.total_amount):.2f}
"""
    
    if last_bill.due_date:
        response += f"**Due Date:** {last_bill.due_date.strftime('%Y-%m-%d')}\n"
    
    if items:
        response += "\n**Invoice Items:**\n"
        for item in items:
            if item.item_type == 'plan' and item.plan:
                response += f"\n📋 {item.plan.name}"
            elif item.item_type == 'extra_cost':
                response += f"\n💸 {item.extra_cost_type}"
                if item.description:
                    response += f" - {item.description}"
            response += f"\n   Amount: €{float(item.amount):.2f}\n"
    
    return {
        'message': response.strip(),
        'state': 'initial',
        'reset': True
    }


def handle_user_message(user_id: str, message: str) -> Dict[str, Any]:
    """Main message handler - routes to appropriate function based on state."""
    sess = get_or_create_session()
    
    # Handle reset/restart commands
    if message.lower() in ['restart', 'reset', 'start', 'menu']:
        clear_session()
        sess = get_or_create_session()
    
    state = sess['state']
    
    # Initial state - present options
    if state == 'initial':
        response = present_options()
        sess['state'] = response['state']
        session.modified = True  # Mark session as modified
        return response
    
    # Waiting for option selection
    elif state == 'awaiting_option':
        option = parse_option(message)
        
        if option is None:
            return {
                'message': '❌ Invalid option. Please enter a number from 1 to 7.',
                'state': 'awaiting_option'
            }
        
        sess['selected_option'] = option
        
        # Handle based on option
        if option == 1:
            response = get_sim_types()
            if response.get('reset'):
                clear_session()
            return response
        
        elif option in [2, 3]:
            response = handle_info_option(option)
            if response.get('reset'):
                clear_session()
            return response
        
        elif option == 4:
            response = handle_update_request()
            sess['state'] = response['state']
            session.modified = True
            return response
        
        elif option == 5:
            response = handle_fetch_request()
            sess['state'] = response['state']
            session.modified = True
            return response
        
        elif option == 6:
            response = handle_open_bills_request()
            sess['state'] = response['state']
            session.modified = True
            return response
        
        elif option == 7:
            response = handle_last_bill_request()
            sess['state'] = response['state']
            session.modified = True
            return response
    
    # Waiting for update data
    elif state == 'awaiting_update_data':
        response = process_update(message)
        if response.get('reset'):
            clear_session()
        else:
            sess['state'] = response['state']
            session.modified = True
        return response
    
    # Waiting for user identifier
    elif state == 'awaiting_identifier':
        response = fetch_user_info(message)
        if response.get('reset'):
            clear_session()
        else:
            sess['state'] = response['state']
            session.modified = True
        return response
    
    # Waiting for BA number for open bills
    elif state == 'awaiting_ba_for_bills':
        response = fetch_open_bills(message)
        if response.get('reset'):
            clear_session()
        else:
            sess['state'] = response['state']
            session.modified = True
        return response
    
    # Waiting for BA number for last bill
    elif state == 'awaiting_ba_for_last_bill':
        response = fetch_last_open_bill(message)
        if response.get('reset'):
            clear_session()
        else:
            sess['state'] = response['state']
            session.modified = True
        return response
    
    # Unknown state - reset
    else:
        clear_session()
        return present_options()
