from flask import Flask
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    # Africastalking
    app.config["username"]=os.getenv("USERNAME")
    app.config["api_key"]=os.getenv("API_KEY")
    # Database
    app.config["db_username"]=os.getenv("DB_USERNAME")
    app.config["pasword"]=os.getenv("PASSWORD")
    app.config["url"]=os.getenv("URL")
    

    from .routes.ussd import ussd_bp
  
    app.register_blueprint(ussd_bp)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
    