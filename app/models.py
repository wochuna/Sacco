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

    def verify_pin(self, raw_pin):
        """Checks if the entered PIN matches the stored hash."""
        return check_password_hash(self.pin, raw_pin)

    def __repr__(self):
        return f"<User {self.phone_number}>"


class Sessions(db.Model):
    __tablename__ = 'sessions'

    session_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    session_start_time = db.Column(db.DateTime, default=db.func.current_timestamp())
    session_end_time = db.Column(db.DateTime, nullable=True)
    last_action = db.Column(db.String(255), nullable=True)

    user = db.relationship('Tests', backref=db.backref('sessions', lazy=True))

    def __init__(self, user_id, last_action=None):
        """Initialize a new session."""
        self.user_id = user_id
        self.last_action = last_action

    def update_last_action(self, action):
        """Updates the last action taken in the session."""
        self.last_action = action
        db.session.commit()

    def end_session(self):
        """Marks the session as ended."""
        self.session_end_time = db.func.current_timestamp()
        db.session.commit()

    def __repr__(self):
        return f"<Session {self.session_id}, User {self.user_id}, Last Action {self.last_action}>"


"""from sqlalchemy import Column, Integer, String, LargeBinary, Enum, Boolean, DateTime, func
class User(db.Model):
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
    