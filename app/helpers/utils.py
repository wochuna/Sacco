import logging
import re
from werkzeug.security import check_password_hash
from flask import make_response, current_app
from app import db
from app.models import Tests, Withdrawals, Transactions

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def mask_sensitive_info(data, visible_start=2, visible_end=2):
    """Mask sensitive information, keeping only a few visible characters."""
    if isinstance(data, str) and len(data) > (visible_start + visible_end):
        return data[:visible_start] + "*" * (len(data) - visible_start - visible_end) + data[-visible_end:]
    return "*" * len(data)

def sanitize_log_message(message):
    """Mask sensitive data in log messages."""
    message = re.sub(r"phone_number='(\d{10,})'", lambda m: f"phone_number='{mask_sensitive_info(m.group(1))}'", message)
    message = re.sub(r"national_id='(\d+)'", lambda m: f"national_id='{mask_sensitive_info(m.group(1))}'", message)
    message = re.sub(r"pin='(\d+)'", lambda m: f"pin='****'", message)
    return message

class MaskingFormatter(logging.Formatter):
    def format(self, record):
        record.msg = sanitize_log_message(str(record.msg))
        return super().format(record)

for handler in logging.getLogger().handlers:
    handler.setFormatter(MaskingFormatter("%(asctime)s - %(levelname)s - %(message)s"))

def validate_phone_number(phone_number):
    """Validate phone number: Must be 10 digits and start with 07."""
    return bool(re.match(r"^07\d{8}$", phone_number))

def validate_national_id(national_id):
    """Validate national ID: Must be 8 or 9 digits."""
    return bool(re.match(r"^\d{8,9}$", national_id))

def validate_pin(pin):
    """Validate pin:Must be 4 digits."""
    return bool(re.match(r"^\d{4}$", pin))

def register_user(phone_number, national_id, pin):
    """Register a new user and start a session."""
    phone_number = normalize_phone_number(phone_number)
    
    # Validate phone number
    if not validate_phone_number(phone_number):
        logging.warning(f"Invalid phone number: '{phone_number}'")
        return {"status": False, "message": "Invalid phone number.Please try again"}

    # Validate national ID
    if not validate_national_id(national_id):
        logging.warning(f"Invalid national ID: '{national_id}'")
        return {"status": False, "message": "Invalid national ID.Please try again"}

    # Validate pin
    if not validate_pin(pin):
        logging.warning(f"Invalid pin:'{pin}'")
        return {"status": False, "message": "Invalid pin.Please try again"}

    existing_user = Tests.query.filter(
        (Tests.phone_number == phone_number) | (Tests.national_id == national_id)
    ).first()

    if existing_user:
        logging.warning(f"Registration failed: User already exists - phone_number='{mask_sensitive_info(phone_number)}'")
        return {"status": False, "message": "User already exists."}

    new_user = Tests(phone_number=phone_number, national_id=national_id)
    new_user.set_pin(pin)

    logging.info(f"Registering user: phone_number='{mask_sensitive_info(phone_number)}'")

    try:
        db.session.add(new_user)
        db.session.commit()
        logging.info(f"User registered successfully: phone_number='{mask_sensitive_info(phone_number)}'")

        return {"status": True, "message": "User registered successfully!"}
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error registering user: {e}")
        return {"status": False, "message": f"Error occurred: {str(e)}"}

def normalize_phone_number(phone_number):
    """Ensure phone numbers are stored and checked in a consistent format."""
    if phone_number.startswith("+254"):
        return "0" + phone_number[4:]
    elif phone_number.startswith("254"):
        return "0" + phone_number[3:]
    return phone_number

def verify_pin(user, pin):
    """Verify the entered PIN against the stored hash."""
    if not user or not user.pin:
        logging.error("PIN verification failed: User not found or no PIN stored.")
        return False

    logging.info(f"Verifying PIN for phone_number='{mask_sensitive_info(user.phone_number)}'")

    if check_password_hash(user.pin, pin):
        logging.info(f"PIN verification successful for phone_number='{mask_sensitive_info(user.phone_number)}'")


        return {"status": True}
    else:
        logging.error(f"Invalid PIN for user phone_number='{mask_sensitive_info(user.phone_number)}'")
        return {"status": False}

def ussd_response(message, status=200):
    """Return a formatted USSD response with UTF-8 encoding."""
    response = make_response(message, status)
    response.headers['Content-Type'] = "text/plain; charset=utf-8"
    return response

def validate_withdrawal(user, amount, pin):
    """Validate if the withdrawal can proceed."""
    if not user:
        return {"status": False, "message": "User not found."}

    # Verify PIN
    pin_verification = verify_pin(user, pin)
    if not pin_verification["status"]:
        return {"status": False, "message": "Incorrect PIN."}

    # Check if user has enough balance
    if user.balance < amount:
        return {"status": False, "message": "Insufficient funds."}

    return {"status": True}

def update_balance(user, amount):
    """Update the user's balance after a successful withdrawal."""
    try:
        user.balance -= amount
        db.session.commit()
        return {"status": True}
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating balance: {e}")
        return {"status": False, "message": "Transaction failed."}

def process_withdrawal(user, amount, pin, account_type, withdrawal_method, provider=None, phone_number=None):

    # Validate Withdrawal
    validation = validate_withdrawal(user, amount, pin)
    if not validation["status"]:
        return validation
    # Withdraw from Sacco Wallet
    if account_type == "sacco_wallet":
        if withdrawal_method == "savings":
            logging.info(f"Transferring {amount} from Sacco Wallet to Savings for user {mask_sensitive_info(user.phone_number)}")
            user.savings_balance += amount  # Add to savings
        elif withdrawal_method == "mobile_money":
            if not provider or not phone_number or not validate_phone_number(phone_number):
                return {"status": False, "message": "Invalid mobile money details."}
            logging.info(f"Withdrawing {amount} from Sacco Wallet to {provider} ({mask_sensitive_info(phone_number)})")

    # Withdraw from Savings
    elif account_type == "savings":
        if withdrawal_method == "sacco_wallet":
            logging.info(f"Transferring {amount} from Savings to Sacco Wallet for user {mask_sensitive_info(user.phone_number)}")
            user.balance += amount
        elif withdrawal_method == "mobile_money":
            if not provider or not phone_number or not validate_phone_number(phone_number):
                return {"status": False, "message": "Invalid mobile money details."}
            logging.info(f"Withdrawing {amount} from Savings to {provider} ({mask_sensitive_info(phone_number)})")

    else:
        return {"status": False, "message": "Invalid account type."}

    # Deduct from original account balance
    balance_update = update_balance(user, amount)
    if not balance_update["status"]:
        return balance_update  # Return balance update failure message

    return {"status": True, "message": "Withdrawal successful."}


def process_deposit(phone_number, amount, source, destination):
    """
    Process deposit transactions.

    :param phone_number: The phone number initiating the deposit.
    :param amount: The amount to deposit.
    :param source: The source of funds (Mobile Money or SACCO Wallet).
    :param destination: The destination account (Savings or SACCO Wallet).
    :return: Dictionary with transaction status and message.
    """
    try:
        # Validate amount
        amount = float(amount)
        if amount <= 0:
            return {"status": False, "message": "Invalid deposit amount."}

        # Find the user
        user = Tests.query.filter_by(phone_number=phone_number).first()
        if not user:
            return {"status": False, "message": "User not found."}

        # Process transaction 
        new_transaction = Transactions(
            phone_number=phone_number,
            amount=amount,
            transaction_type="deposit",
            source=source,
            destination=destination,
        )

        db.session.add(new_transaction)
        db.session.commit()

        logging.info(f"Deposit successful: {amount} from {source} to {destination} for {phone_number}")

        return {"status": True, "message": f"Deposit of KES {amount} to {destination} successful."}

    except Exception as e:
        logging.error(f"Error processing deposit: {str(e)}")
        return {"status": False, "message": "An error occurred. Please try again."}
