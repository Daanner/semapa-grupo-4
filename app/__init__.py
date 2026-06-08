from flask import Flask
from flask_sqlalchemy import SQLAlchemy ############
from config import config

db = SQLAlchemy()#########

def create_app(config_name="default"):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config[config_name])
    
    db.init_app(app)

    # ── Blueprints ──────────────────────────────────────────
    from app.dashboard.routes import dashboard_bp
    from app.mensajeria.routes import mensajeria_bp
    from app.pdf.routes import pdf_bp
    from app.totem.routes import totem_bp
    from app.lector.routes import lector_bp

    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(mensajeria_bp, url_prefix="/mensajeria")
    app.register_blueprint(pdf_bp, url_prefix="/pdf")
    app.register_blueprint(totem_bp, url_prefix="/totem")
    app.register_blueprint(lector_bp, url_prefix="/lector")

    # ── Index ────────────────────────────────────────────────
    from flask import render_template
    @app.route("/")
    def index():
        return render_template("index.html")

    return app
