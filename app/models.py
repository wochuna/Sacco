#from sqlalchemy import Column, Integer, String, LargeBinary, Enum, Boolean, DateTime, func
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class Tests(db.Model):
    __tablename__ = 'tests'

    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    national_id = db.Column(db.String(20), unique=True, nullable=False)
    pin = db.Column(db.String(128), nullable=False)
    shares_amount = db.Column(db.Float, default=0.0)
    savings_amount = db.Column(db.Float, default=0.0)

    def set_pin(self, raw_pin):
        """Hashes the PIN before storing it."""
        self.pin = generate_password_hash(raw_pin)
        print(self.pin)

    def verify_pin(self, raw_pin):
        """Checks if the entered PIN matches the stored hash."""
        return check_password_hash(str(self.pin), raw_pin)

    def __repr__(self):
        return f"<User {self.phone_number}>"


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
    