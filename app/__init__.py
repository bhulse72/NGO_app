from flask import Flask, render_template, session

def create_app():
    app = Flask(__name__)

    from config import SECRET_KEY
    app.secret_key = SECRET_KEY

    from app.routes.contacts import contacts_bp
    from app.routes.clients import clients_bp
    from app.routes.social_workers import social_workers_bp
    from app.routes.time_logs import time_logs_bp
    from app.routes.reports import reports_bp
    from app.routes.auth import auth_bp
    app.register_blueprint(contacts_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(social_workers_bp)
    app.register_blueprint(time_logs_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(auth_bp)

    @app.context_processor
    def inject_user():
        from config import USERS
        username = session.get("username")
        current_user = USERS.get(username) if username else None
        return {"current_user": current_user, "username": username}

    @app.route("/")
    def index():
        from app.services.sheets_service import load_all_contacts, load_all_clients, load_all_social_workers
        contacts = load_all_contacts()
        clients = load_all_clients()
        workers = load_all_social_workers()
        stats = {
            "total_contacts": len(contacts),
            "total_clients": len(clients),
            "active_clients": len([c for c in clients if c.is_active]),
            "urgent_clients": len([c for c in clients if c.risk_level == "Needs urgent help"]),
        }
        recent_contacts = sorted(contacts, key=lambda c: c.date_added, reverse=True)[:5]
        recent_clients = sorted(clients, key=lambda c: c.client_since, reverse=True)[:5]
        return render_template("index.html", stats=stats, recent_contacts=recent_contacts, recent_clients=recent_clients, workers=workers)

    return app