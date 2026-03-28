from flask import Flask

def create_app():
    app = Flask(__name__)

    from app.routes.contacts import contacts_bp
    from app.routes.clients import clients_bp
    app.register_blueprint(contacts_bp)
    app.register_blueprint(clients_bp)

    @app.route("/")
    def index():
        return "NGO app is running!"

    return app