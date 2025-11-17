from flask import Blueprint, render_template

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
