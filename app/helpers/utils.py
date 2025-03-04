import logging
import os
import mysql.connector
from werkzeug.security import check_password_hash
from flask import make_response, current_app
from app import db
from app.models import Tests

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def mask_sensitive_info(data, visible_start=4, visible_end=2):
    """Mask sensitive information, showing only the first few and last few characters."""
    if len(data) <= (visible_start + visible_end):
        return "*" * len(data)#mask everything for short data
    return data[:visible_start] + "x" * (len(data) - (visible_start + visible_end)) + data[-visible_end:]

def register_user(phone_number, national_id, pin):
    """Register a new user while logging actions and handling errors."""
    phone_number = normalize_phone_number(phone_number)

    existing_user = Tests.query.filter(
        (Tests.phone_number == phone_number) | (Tests.national_id == national_id)
    ).first()

    if existing_user:
        logging.warning(f"Registration failed: User already exists - {phone_number} or {national_id}")
        return {"status": False, "message": "User with this phone number or national ID already exists."}

    new_user = Tests(phone_number=phone_number, national_id=national_id, pin = pin)
    new_user.set_pin(pin)

    logging.info(f"Registering user: {phone_number}, Hashed PIN: {new_user.pin}")

    try:
        db.session.add(new_user)
        db.session.commit()
        logging.info(f"User registered successfully: {phone_number}")
        return {"status": True, "message": "User registered successfully!", "phone_number": phone_number}
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error registering user: {e}")
        return {"status": False, "message": f"Error occurred while registering user: {str(e)}"}

def normalize_phone_number(phone_number):
    """Ensure phone numbers are stored and checked in a consistent format."""
    if phone_number.startswith("+254"):
        return "0" + phone_number[4:]
    elif phone_number.startswith("254"):
        return "0" + phone_number[3:]
    return phone_number

def verify_pin(user, pin):
    """Verify the entered PIN against the stored hash with logging."""
    if not user or not user.pin:
        logging.error("PIN verification failed: User not found or no PIN stored.")
        return False

    logging.info(f"Verifying PIN for {user.phone_number}")

    if check_password_hash(user.pin, pin):
        logging.info(f"PIN verification successful for {user.phone_number}")
        return True
    else:
        logging.error(f"Invalid PIN for user {user.phone_number}")
        return False

def ussd_response(message, status=200):
    """Return a formatted USSD response with UTF-8 encoding."""
    response = make_response(message, status)
    response.headers['Content-Type'] = "text/plain; charset=utf-8"
    return response

def my_data():
    """Establish and return a MySQL database connection."""
    try:
        conn = mysql.connector.connect(
            host=current_app.config.get('host', 'localhost'),
            database="saccos",
            user=current_app.config.get('db_username', 'root'),
            password=current_app.config.get('db_password', ''),
            collation="utf8mb4_general_ci"
        )
        if conn.is_connected():
            logging.info("Connected to MySQL Database")
        return conn
    except mysql.connector.Error as e:
        logging.error(f"Error connecting to MySQL: {e}")
        return None
