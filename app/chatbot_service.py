"""Chatbot service for handling user conversations."""
from typing import Dict, Any, Optional
from datetime import datetime
from flask import session
from .extensions import db
from .models import Customer, Sim, Assignment, SimType, BillingAccount, Bill, InvoiceItem


OPTIONS = {
    1: "Tell me which type of SIM cards I can get in your company",
    2: "I want to change my personal information",
    3: "Retrieve User Information",
    4: "Give me my open bills",
    5: "Give me my last open bill"
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
    options_text += "\nReply with a number (1-5) to select an option."
    
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
        if option in OPTIONS:
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
                'message': 'No SIM types available at the moment.',
                'state': 'initial',
                'reset': True
            }
        
        response = "**Available SIM Card Types:**\n\n"
        for sim_type in sim_types:
            price_str = f"EUR {float(sim_type.price):.2f}" if sim_type.price > 0 else "FREE"
            response += f"**{sim_type.name}**\n"
            if sim_type.description:
                response += f"   {sim_type.description}\n"
            response += f"   Price: {price_str}\n\n"
        
        # Append main menu
        response += "\n\n---\n\n**What can I help you with?**\n\n"
        for num, desc in OPTIONS.items():
            response += f"{num}. {desc}\n"
        response += "\nReply with a number (1-5) to select an option."
        
        return {
            'message': response.strip(),
            'state': 'awaiting_option',
            'reset': True
        }
    except Exception as e:
        return {
            'message': f'Error fetching SIM types: {str(e)}',
            'state': 'initial',
            'reset': True
        }


def handle_update_request() -> Dict[str, Any]:
    """Handle option 4 - request OIB for personal information update."""
    return {
        'message': """**Update Personal Information**

Please provide your OIB (11-digit identification number), or send 0 to return to the main menu:""",
        'state': 'awaiting_oib_for_update'
    }


def verify_oib_and_prompt_field(oib: str) -> Dict[str, Any]:
    """Verify OIB and prompt for field to update."""
    oib = oib.strip().replace('-', '').replace(' ', '')
    
    # Validate OIB format (11 digits)
    if not oib.isdigit() or len(oib) != 11:
        return {
            'message': 'Invalid OIB format. Please provide an 11-digit OIB number, or send 0 to return to the main menu.',
            'state': 'awaiting_oib_for_update'
        }
    
    try:
        customer = db.session.query(Customer).filter(Customer.oib == oib).first()
        
        if not customer:
            response = f"""No customer found with OIB: {oib}

---

**What can I help you with?**\n\n"""
            for num, desc in OPTIONS.items():
                response += f"{num}. {desc}\n"
            response += "\nReply with a number (1-5) to select an option."
            return {
                'message': response,
                'state': 'awaiting_option',
                'reset': True
            }
        
        return {
            'message': f"""**Customer Found**

**Name:** {customer.name}
**Email:** {customer.email or 'N/A'}

What would you like to update?
1. Name
2. Email

Reply with 1 or 2, or send 0 to return to the main menu:""",
            'state': 'awaiting_field_selection',
            'context': {'customer_id': customer.id, 'oib': oib}
        }
    except Exception as e:
        response = f"""Database error: {str(e)}

---

**What can I help you with?**\n\n"""
        for num, desc in OPTIONS.items():
            response += f"{num}. {desc}\n"
        response += "\nReply with a number (1-5) to select an option."
        return {
            'message': response,
            'state': 'awaiting_option',
            'reset': True
        }


def handle_field_selection(message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle field selection for update."""
    choice = message.strip()
    
    if choice == '1':
        return {
            'message': 'Please enter your new **name**, or send 0 to return to the main menu:',
            'state': 'awaiting_name_update',
            'context': context
        }
    elif choice == '2':
        return {
            'message': 'Please enter your new **email address**, or send 0 to return to the main menu:',
            'state': 'awaiting_email_update',
            'context': context
        }
    else:
        return {
            'message': 'Invalid choice. Please reply with 1 (Name) or 2 (Email), or send 0 to return to the main menu:',
            'state': 'awaiting_field_selection',
            'context': context
        }


def update_customer_name(customer_id: int, new_name: str) -> Dict[str, Any]:
    """Update customer name."""
    try:
        customer = db.session.get(Customer, customer_id)
        
        if not customer:
            response = """Customer not found.

---

**What can I help you with?**\n\n"""
            for num, desc in OPTIONS.items():
                response += f"{num}. {desc}\n"
            response += "\nReply with a number (1-5) to select an option."
            return {
                'message': response,
                'state': 'awaiting_option',
                'reset': True
            }
        
        old_name = customer.name
        customer.name = new_name.strip()
        db.session.commit()
        
        response = f"""**Name Updated Successfully!**

**Old Name:** {old_name}
**New Name:** {customer.name}

---

**What can I help you with?**\n\n"""
        for num, desc in OPTIONS.items():
            response += f"{num}. {desc}\n"
        response += "\nReply with a number (1-5) to select an option."
        
        return {
            'message': response,
            'state': 'awaiting_option',
            'reset': True
        }
    except Exception as e:
        db.session.rollback()
        response = f"""Database error: {str(e)}

---

**What can I help you with?**\n\n"""
        for num, desc in OPTIONS.items():
            response += f"{num}. {desc}\n"
        response += "\nReply with a number (1-5) to select an option."
        return {
            'message': response,
            'state': 'awaiting_option',
            'reset': True
        }


def update_customer_email(customer_id: int, new_email: str) -> Dict[str, Any]:
    """Update customer email."""
    try:
        customer = db.session.get(Customer, customer_id)
        
        if not customer:
            response = """Customer not found.

---

**What can I help you with?**\n\n"""
            for num, desc in OPTIONS.items():
                response += f"{num}. {desc}\n"
            response += "\nReply with a number (1-5) to select an option."
            return {
                'message': response,
                'state': 'awaiting_option',
                'reset': True
            }
        
        # Check for duplicate email
        existing = db.session.query(Customer).filter(
            Customer.email == new_email.strip(),
            Customer.id != customer_id
        ).first()
        
        if existing:
            response = f"""Email {new_email} is already in use by another customer.

---

**What can I help you with?**\n\n"""
            for num, desc in OPTIONS.items():
                response += f"{num}. {desc}\n"
            response += "\nReply with a number (1-5) to select an option."
            return {
                'message': response,
                'state': 'awaiting_option',
                'reset': True
            }
        
        old_email = customer.email
        customer.email = new_email.strip()
        db.session.commit()
        
        response = f"""**Email Updated Successfully!**

**Old Email:** {old_email or 'N/A'}
**New Email:** {customer.email}

---

**What can I help you with?**\n\n"""
        for num, desc in OPTIONS.items():
            response += f"{num}. {desc}\n"
        response += "\nReply with a number (1-5) to select an option."
        
        return {
            'message': response,
            'state': 'awaiting_option',
            'reset': True
        }
    except Exception as e:
        db.session.rollback()
        response = f"""Database error: {str(e)}

---

**What can I help you with?**\n\n"""
        for num, desc in OPTIONS.items():
            response += f"{num}. {desc}\n"
        response += "\nReply with a number (1-5) to select an option."
        return {
            'message': response,
            'state': 'awaiting_option',
            'reset': True
        }


def handle_fetch_request() -> Dict[str, Any]:
    """Handle option 3 - request OIB for user info fetch."""
    return {
        'message': """**Retrieve User Information**

Please provide your **OIB (11 digits)**.

Or send 0 to return to the main menu.""",
        'state': 'awaiting_identifier'
    }


def fetch_user_info(message: str) -> Dict[str, Any]:
    """Fetch and display user information by OIB only."""
    identifier = message.strip()

    if identifier == '0':
        response = """Returning to the main menu.

**What can I help you with?**\n\n"""
        for num, desc in OPTIONS.items():
            response += f"{num}. {desc}\n"
        response += "\nReply with a number (1-5) to select an option."
        return {
            'message': response,
            'state': 'awaiting_option',
            'reset': True
        }

    # Validate OIB format
    is_valid, error = validate_oib(identifier)
    if not is_valid:
        return {
            'message': f"{error} Please provide a valid 11-digit OIB, or send 0 to return to the main menu.",
            'state': 'awaiting_identifier'
        }

    customer = db.session.query(Customer).filter(Customer.oib == identifier).first()

    if not customer:
        response = f"""No customer found with OIB: {identifier}

---

**What can I help you with?**\n\n"""
        for num, desc in OPTIONS.items():
            response += f"{num}. {desc}\n"
        response += "\nReply with a number (1-5) to select an option."
        return {
            'message': response,
            'state': 'awaiting_option',
            'reset': True
        }
    
    # Fetch assigned SIMs
    assignments = db.session.query(Assignment, Sim).join(
        Sim, Assignment.sim_id == Sim.id
    ).filter(Assignment.customer_id == customer.id).all()
    
    # Build response
    response = f"""**Customer Information**

**ID:** {customer.id}
**Name:** {customer.name}
**Email:** {customer.email or 'N/A'}
**OIB:** {customer.oib}
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
    
    # Append main menu
    response += "\n\n---\n\n**What can I help you with?**\n\n"
    for num, desc in OPTIONS.items():
        response += f"{num}. {desc}\n"
    response += "\nReply with a number (1-5) to select an option."
    
    return {
        'message': response,
        'state': 'awaiting_option',
        'reset': True
    }


def handle_open_bills_request() -> Dict[str, Any]:
    """Handle option 4 - request BA for open bills."""
    return {
        'message': """**View Open Bills**

Please provide your Billing Account number (e.g., `9001242277`), or send 0 to return to the main menu:""",
        'state': 'awaiting_ba_for_bills'
    }


def handle_last_bill_request() -> Dict[str, Any]:
    """Handle option 5 - request BA for last open bill."""
    return {
        'message': """**View Last Open Bill**

Please provide your Billing Account number (e.g., `9001242277`), or send 0 to return to the main menu:""",
        'state': 'awaiting_ba_for_last_bill'
    }


def validate_ba_number(ba_number: str) -> tuple[bool, Optional[str]]:
    """Validate billing account number format.
    
    Returns:
        (is_valid, error_message)
    """
    ba_number = ba_number.strip()
    
    # Check if it's exactly 10 digits
    if not ba_number.isdigit():
        return False, "Billing Account number must contain only digits."
    
    if len(ba_number) != 10:
        return False, f"Billing Account number must be exactly 10 digits. You provided {len(ba_number)}."
    
    # Check if it starts with 900
    if not ba_number.startswith('900'):
        return False, "Billing Account number must start with 900."
    
    return True, None


def validate_oib(oib: str) -> tuple[bool, Optional[str]]:
    """Validate Croatian OIB (Osobni Identifikacijski Broj) using ISO 7064, MOD 11-10.
    
    Returns:
        (is_valid, error_message)
    """
    oib = oib.strip()
    
    # Check if it's exactly 11 digits
    if not oib.isdigit():
        return False, "OIB must contain only digits."
    
    if len(oib) != 11:
        return False, f"OIB must be exactly 11 digits. You provided {len(oib)}."
    
    # Validate check digit using ISO 7064, MOD 11-10 algorithm
    a = 10
    for i in range(10):
        a = a + int(oib[i])
        a = a % 10
        if a == 0:
            a = 10
        a = (a * 2) % 11
    
    check_digit = (11 - a) % 10
    if check_digit != int(oib[10]):
        return False, "Invalid OIB check digit. Please verify the number."
    
    return True, None


def generate_valid_oib(base: str = None) -> str:
    """Generate a valid Croatian OIB.
    
    Args:
        base: Optional 10-digit base. If None, generates random base.
    
    Returns:
        Valid 11-digit OIB string
    """
    import random
    
    if base is None:
        base = ''.join([str(random.randint(0, 9)) for _ in range(10)])
    elif len(base) != 10 or not base.isdigit():
        raise ValueError("Base must be exactly 10 digits")
    
    # Calculate check digit
    a = 10
    for digit in base:
        a = a + int(digit)
        a = a % 10
        if a == 0:
            a = 10
        a = (a * 2) % 11
    
    check_digit = (11 - a) % 10
    return base + str(check_digit)


def fetch_open_bills(ba_number: str) -> Dict[str, Any]:
    """Fetch and display all open bills for a billing account."""
    ba_number = ba_number.strip()
    
    # Validate BA number format
    is_valid, error_msg = validate_ba_number(ba_number)
    if not is_valid:
        return {
            'message': error_msg + ' Or send 0 to return to the main menu.',
            'state': 'awaiting_ba_for_bills'
        }
    
    # Find billing account
    billing_account = db.session.query(BillingAccount).filter(
        BillingAccount.account_number == ba_number
    ).first()
    
    if not billing_account:
        response = f"""No billing account found with number: {ba_number}

    ---

    **What can I help you with?**\n\n"""
        for num, desc in OPTIONS.items():
            response += f"{num}. {desc}\n"
        response += "\nReply with a number (1-5) to select an option."
        return {
            'message': response,
            'state': 'awaiting_option',
            'reset': True
        }
    
    # Fetch open bills (pending or overdue)
    open_bills = db.session.query(Bill).filter(
        Bill.billing_account_id == billing_account.id,
        Bill.status.in_(['pending', 'overdue'])
    ).order_by(Bill.bill_month.desc()).all()
    
    if not open_bills:
        response = f"""**No Open Bills**

**Billing Account:** {ba_number}
**Customer:** {billing_account.customer.name}

You have no open bills at this time.

---

**What can I help you with?**\n\n"""
        for num, desc in OPTIONS.items():
            response += f"{num}. {desc}\n"
        response += "\nReply with a number (1-5) to select an option."
        return {
            'message': response,
            'state': 'awaiting_option',
            'reset': True
        }
    
    # Build response
    response = f"""**Open Bills**

**Billing Account:** {ba_number}
**Customer:** {billing_account.customer.name}
**Number of Open Bills:** {len(open_bills)}

"""
    
    for bill in open_bills:
        status_label = "OVERDUE" if bill.status == 'overdue' else "PENDING"
        response += f"\n[{status_label}] **{bill.bill_month}**"
        response += f"\n   Amount: EUR {float(bill.total_amount):.2f}"
        response += f"\n   Status: {bill.status.capitalize()}"
        if bill.due_date:
            response += f"\n   Due: {bill.due_date.strftime('%Y-%m-%d')}"
        response += "\n"
    
    # Append main menu
    response += "\n---\n\n**What can I help you with?**\n\n"
    for num, desc in OPTIONS.items():
        response += f"{num}. {desc}\n"
    response += "\nReply with a number (1-5) to select an option."
    
    return {
        'message': response.strip(),
        'state': 'awaiting_option',
        'reset': True
    }


def fetch_last_open_bill(ba_number: str) -> Dict[str, Any]:
    """Fetch and display the most recent open bill for a billing account."""
    ba_number = ba_number.strip()
    
    # Validate BA number format
    is_valid, error_msg = validate_ba_number(ba_number)
    if not is_valid:
        return {
            'message': error_msg + ' Or send 0 to return to the main menu.',
            'state': 'awaiting_ba_for_last_bill'
        }
    
    # Find billing account
    billing_account = db.session.query(BillingAccount).filter(
        BillingAccount.account_number == ba_number
    ).first()
    
    if not billing_account:
        response = f"""No billing account found with number: {ba_number}

---

**What can I help you with?**\n\n"""
        for num, desc in OPTIONS.items():
            response += f"{num}. {desc}\n"
        response += "\nReply with a number (1-5) to select an option."
        return {
            'message': response,
            'state': 'awaiting_option',
            'reset': True
        }
    
    # Fetch most recent open bill
    last_bill = db.session.query(Bill).filter(
        Bill.billing_account_id == billing_account.id,
        Bill.status.in_(['pending', 'overdue'])
    ).order_by(Bill.bill_month.desc()).first()
    
    if not last_bill:
        response = f"""**No Open Bills**

**Billing Account:** {ba_number}
**Customer:** {billing_account.customer.name}

You have no open bills at this time.

---

**What can I help you with?**\n\n"""
        for num, desc in OPTIONS.items():
            response += f"{num}. {desc}\n"
        response += "\nReply with a number (1-5) to select an option."
        return {
            'message': response,
            'state': 'awaiting_option',
            'reset': True
        }
    
    # Fetch invoice items for this bill
    items = db.session.query(InvoiceItem).filter(
        InvoiceItem.bill_id == last_bill.id
    ).all()
    
    # Build response
    status_label = "OVERDUE" if last_bill.status == 'overdue' else "PENDING"
    response = f"""**Latest Open Bill**

**Billing Account:** {ba_number}
**Customer:** {billing_account.customer.name}

[ {status_label} ] **Bill for {last_bill.bill_month}**
**Status:** {last_bill.status.capitalize()}
**Total Amount:** EUR {float(last_bill.total_amount):.2f}
"""
    
    if last_bill.due_date:
        response += f"**Due Date:** {last_bill.due_date.strftime('%Y-%m-%d')}\n"
    
    if items:
        response += "\n**Invoice Items:**\n"
        for item in items:
            if item.item_type == 'plan' and item.plan:
                response += f"\n- Plan: {item.plan.name}"
            elif item.item_type == 'extra_cost':
                response += f"\n- Extra cost: {item.extra_cost_type}"
                if item.description:
                    response += f" - {item.description}"
            response += f"\n   Amount: EUR {float(item.amount):.2f}\n"
    
    # Append main menu
    response += "\n---\n\n**What can I help you with?**\n\n"
    for num, desc in OPTIONS.items():
        response += f"{num}. {desc}\n"
    response += "\nReply with a number (1-5) to select an option."
    
    return {
        'message': response.strip(),
        'state': 'awaiting_option',
        'reset': True
    }


def handle_user_message(user_id: str, message: str) -> Dict[str, Any]:
    """Main message handler - routes to appropriate function based on state."""
    sess = get_or_create_session()
    
    # Handle reset/restart commands and return to menu with 0
    if message.lower() in ['restart', 'reset', 'start', 'menu'] or message.strip() == '0':
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
                'message': 'Invalid option. Please enter a valid number (1-5), or send 0 to return to the main menu.',
                'state': 'awaiting_option'
            }
        
        sess['selected_option'] = option
        
        # Handle based on option
        if option == 1:
            response = get_sim_types()
            if response.get('reset'):
                clear_session()
                sess = get_or_create_session()
                sess['state'] = response['state']
                session.modified = True
            return response
        
        elif option == 2:
            response = handle_update_request()
            sess['state'] = response['state']
            session.modified = True
            return response
        
        elif option == 3:
            response = handle_fetch_request()
            sess['state'] = response['state']
            session.modified = True
            return response
        
        elif option == 4:
            response = handle_open_bills_request()
            sess['state'] = response['state']
            session.modified = True
            return response
        
        elif option == 5:
            response = handle_last_bill_request()
            sess['state'] = response['state']
            session.modified = True
            return response
        
        # Fallback for unexpected option values
        else:
            return {
                'message': 'Invalid option. Please enter a valid number (1-5).',
                'state': 'awaiting_option'
            }
    
    # Waiting for OIB for personal info update
    elif state == 'awaiting_oib_for_update':
        response = verify_oib_and_prompt_field(message)
        if response.get('reset'):
            clear_session()
            sess = get_or_create_session()
            sess['state'] = response['state']
            session.modified = True
        else:
            sess['state'] = response['state']
            if 'context' in response:
                sess['context'] = response['context']
            session.modified = True
        return response
    
    # Waiting for field selection (name or email)
    elif state == 'awaiting_field_selection':
        response = handle_field_selection(message, sess.get('context', {}))
        if response.get('reset'):
            clear_session()
            sess = get_or_create_session()
            sess['state'] = response['state']
            session.modified = True
        else:
            sess['state'] = response['state']
            if 'context' in response:
                sess['context'] = response['context']
            session.modified = True
        return response
    
    # Waiting for new name
    elif state == 'awaiting_name_update':
        customer_id = sess.get('context', {}).get('customer_id')
        if customer_id:
            response = update_customer_name(customer_id, message)
            if response.get('reset'):
                clear_session()
                sess = get_or_create_session()
                sess['state'] = response['state']
                session.modified = True
            else:
                sess['state'] = response['state']
                session.modified = True
            return response
        else:
            clear_session()
            return present_options()
    
    # Waiting for new email
    elif state == 'awaiting_email_update':
        customer_id = sess.get('context', {}).get('customer_id')
        if customer_id:
            response = update_customer_email(customer_id, message)
            if response.get('reset'):
                clear_session()
                sess = get_or_create_session()
                sess['state'] = response['state']
                session.modified = True
            else:
                sess['state'] = response['state']
                session.modified = True
            return response
        else:
            clear_session()
            return present_options()
    
    # Waiting for user identifier
    elif state == 'awaiting_identifier':
        response = fetch_user_info(message)
        if response.get('reset'):
            clear_session()
            sess = get_or_create_session()
            sess['state'] = response['state']
            session.modified = True
        else:
            sess['state'] = response['state']
            session.modified = True
        return response
    
    # Waiting for BA number for open bills
    elif state == 'awaiting_ba_for_bills':
        response = fetch_open_bills(message)
        if response.get('reset'):
            clear_session()
            sess = get_or_create_session()
            sess['state'] = response['state']
            session.modified = True
        else:
            sess['state'] = response['state']
            session.modified = True
        return response
    
    # Waiting for BA number for last bill
    elif state == 'awaiting_ba_for_last_bill':
        response = fetch_last_open_bill(message)
        if response.get('reset'):
            clear_session()
            sess = get_or_create_session()
            sess['state'] = response['state']
            session.modified = True
        else:
            sess['state'] = response['state']
            session.modified = True
        return response
    
    # Unknown state - reset
    else:
        clear_session()
        return present_options()
