from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Africastalking and Database configuration
    app.config["username"] = os.getenv("username")
    app.config["api_key"] = os.getenv("api_key")
    app.config["db_password"] = os.getenv("db_password")
    app.config["host"] = os.getenv("host")
    app.config["db_username"] = os.getenv("db_username")

    # SQLAlchemy database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{os.getenv("db_username")}:{os.getenv("db_password")}@{os.getenv("host")}/saccos'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize SQLAlchemy with the app
    db.init_app(app)

    from app.routes.ussd_routes import ussd_bp
    app.register_blueprint(ussd_bp, url_prefix="/api")


    with app.app_context():
        from app.models import Tests
        if os.getenv("FLASK_ENV") == "development":
            db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
