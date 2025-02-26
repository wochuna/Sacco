#from sqlalchemy import Column, Integer, String, LargeBinary, Enum, Boolean, DateTime, func
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class Tests(db.Model):
    __tablename__ = 'tests'

    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    national_id = db.Column(db.String(20), unique=True, nullable=False)
    pin = db.Column(db.String(128), nullable=False)
    shares_amount = db.Column(db.Float, default=0.0)
    savings_amount = db.Column(db.Float, default=0.0)

    def set_pin(self, pin):
        """Hash and store the user's PIN securely."""
        if not isinstance(pin, str):
            raise ValueError("PIN must be a string")
        self.pin = generate_password_hash(pin)
        logging.info(f"Setting PIN for {self.phone_number}: {self.pin}")  # Log hashed PIN

    def verify_pin(self, pin):
        """Verify the entered PIN against the stored hash."""
        if not isinstance(self.pin, str):
            logging.error(f"Stored PIN for user {self.phone_number} is not a string!")
            return False

        logging.info(f"Verifying PIN for {self.phone_number}. Entered: {pin}, Stored Hash: {self.pin}")

        if check_password_hash(self.pin, pin):
            logging.info(f"PIN verification successful for {self.phone_number}")
            return True
        else:
            logging.error(f"Invalid PIN for user {self.phone_number}. Entered PIN: '{pin}', Stored Hash: '{self.pin}'")
            return False
        




"""class User(db.Model):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(15), unique=True, nullable=False)
    pin = Column(LargeBinary, nullable=False)
    account_number = Column(Integer, nullable=True)
    status = Column(Enum('Active', 'Inactive'), nullable=False)
    otp = Column(String(6), nullable=True)
    otp_valid = Column(Boolean, default=False)
    otp_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())"""
