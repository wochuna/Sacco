from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

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

class Withdrawals(db.Model):
    __tablename__ = 'withdrawals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('tests.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    withdrawal_method = db.Column(db.Enum('savings', 'mobile_money', name='withdrawal_method'), nullable=False)
    provider = db.Column(db.String(50), nullable=True)
    phone_number = db.Column(db.String(15), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('Tests', backref=db.backref('withdrawals', lazy=True, cascade="all, delete"))

    def __repr__(self):
        return f"<Withdrawal {self.id} - User {self.user_id} - Amount {self.amount}>"

class Transactions(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('tests.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.Enum('deposit', 'withdrawal', 'transfer', name='transaction_type'), nullable=False)
    source = db.Column(db.Enum('mobile_money', 'sacco_wallet', name='transaction_source'), nullable=False)
    destination = db.Column(db.Enum('savings', 'sacco_wallet', 'mobile_money', name='transaction_destination'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('Tests', backref=db.backref('transactions', lazy=True))

    def __repr__(self):
        return f"<Transaction {self.id} - {self.transaction_type} - Amount {self.amount}>"
