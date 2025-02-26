from werkzeug.security import generate_password_hash
from app import db
from app.models import Tests
import logging

def register_user(phone_number, national_id, pin):
    existing_user = Tests.query.filter(
        (Tests.phone_number == phone_number) | (Tests.national_id == national_id)
    ).first()

    if existing_user:
        return {"status": False, "message": "User with this phone number or national ID already exists."}

    # Ensure the PIN is not already hashed
    if "$" in pin:  # Checking if the PIN looks already hashed
        logging.error("PIN appears to be already hashed! Skipping hashing to prevent double hashing.")
    else:
        pin = generate_password_hash(pin)  # Hash the PIN properly

    logging.info(f"Registering user: {phone_number}, Hashed PIN: {pin}")  # Log hashed PIN

    new_user = Tests(phone_number=phone_number, national_id=national_id, pin=pin)

    try:
        db.session.add(new_user)
        db.session.commit()
        logging.info(f"User registered successfully: {phone_number}")
        return {"status": True, "message": "User registered successfully!", "phone_number": phone_number}
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error registering user: {e}")
        return {"status": False, "message": f"Error occurred while registering user: {str(e)}"}
