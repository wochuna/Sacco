from flask import Flask
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config["username"]=os.getenv("USERNAME")
    app.config["api_key"]=os.getenv("API_KEY")
    
    from .routes.ussd import ussd_bp
    
    app.register_blueprint(ussd_bp)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)