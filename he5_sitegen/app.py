from flask import Flask
from config import Config
from extensions import db, login_manager
from routes.generate import generate_bp
from routes.contact import contact_bp
from models import User


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(generate_bp)
    app.register_blueprint(contact_bp)

    with app.app_context():
        db.create_all()

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route("/")
    def index():
        return "HE5 SiteGen is running. Visit /generate to build a site."

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
