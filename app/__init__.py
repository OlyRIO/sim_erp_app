import os
from flask import Flask
from .extensions import db
import click


def create_app() -> Flask:
    app = Flask(__name__)

    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///instance/dev.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Session configuration for chatbot
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    db.init_app(app)

    from .routes import core_bp
    from .api import api_bp

    app.register_blueprint(core_bp)
    app.register_blueprint(api_bp)

    # Optionally seed data on startup if DB is empty
    seed_flag = os.getenv("SEED_ON_START")
    if seed_flag:
        try:
            from .seed import seed_bulk

            with app.app_context():
                print("Starting database seeding...")
                # Use seed_bulk with reset to ensure clean data
                c, s, a = seed_bulk(num_customers=50, num_sims=50, num_assignments=50, reset=True)
                print(f"Database seeding completed: {c} customers, {s} SIMs, {a} assignments")
        except Exception as e:
            # Ignore seeding failures during startup (e.g., before migrations)
            print(f"Seeding failed: {e}")
            import traceback
            traceback.print_exc()
            pass

    @app.cli.command("seed")
    @click.option("--customers", default=1000, show_default=True, type=int, help="Number of customers to create")
    @click.option("--sims", default=1000, show_default=True, type=int, help="Number of sims to create")
    @click.option("--assignments", default=1000, show_default=True, type=int, help="Number of assignments to create")
    @click.option("--reset", is_flag=True, help="Clear existing data before seeding")
    def seed_command(customers: int, sims: int, assignments: int, reset: bool) -> None:
        """Seed the database with dummy data via CLI."""
        from .seed import seed_bulk

        click.echo(f"Seeding: customers={customers}, sims={sims}, assignments={assignments}, reset={reset}")
        with app.app_context():
            c, s, a = seed_bulk(num_customers=customers, num_sims=sims, num_assignments=assignments, reset=reset)
        click.echo(f"Inserted -> customers={c}, sims={s}, assignments={a}")

    return app
