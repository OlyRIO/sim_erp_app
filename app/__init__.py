from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    from .routes import core_bp

    app.register_blueprint(core_bp)

    return app
