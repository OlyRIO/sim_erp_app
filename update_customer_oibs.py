"""Update existing customers with valid OIB numbers."""
import random
from app import create_app
from app.extensions import db
from app.models import Customer


def generate_valid_oib(base: str = None) -> str:
    """Generate a valid Croatian OIB using ISO 7064, MOD 11-10 algorithm."""
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


def main():
    app = create_app()
    with app.app_context():
        # Find all customers without OIB
        customers = Customer.query.filter(Customer.oib.is_(None)).all()
        
        if not customers:
            print("No customers need OIB update.")
            return
        
        print(f"Found {len(customers)} customers without OIB.")
        print("Updating...")
        
        updated = 0
        for customer in customers:
            customer.oib = generate_valid_oib()
            updated += 1
            
            if updated % 100 == 0:
                print(f"Updated {updated} customers...")
        
        db.session.commit()
        print(f"\n✓ Successfully updated {updated} customers with valid OIBs.")
        
        # Show some samples
        samples = Customer.query.limit(5).all()
        print("\nSample customers:")
        for c in samples:
            print(f"  - {c.name}: OIB {c.oib}")


if __name__ == '__main__':
    main()
