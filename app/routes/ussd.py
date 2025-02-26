from flask import Flask, request, Blueprint, make_response
from werkzeug.security import check_password_hash
from app.services import register_user
import logging
from app import db
from app.models import Tests

ussd_bp = Blueprint('ussd', __name__)

def normalize_phone_number(phone_number):
    """Ensure phone numbers are stored and checked in a consistent format."""
    if phone_number.startswith("+254"):
        return "0" + phone_number[4:]
    elif phone_number.startswith("254"):
        return "0" + phone_number[3:]
    return phone_number

@ussd_bp.route('/ussd/callback', methods=['POST', 'GET'])
def ussd_callbacks():
    session_id = request.values.get("sessionId", None)
    service_code = request.values.get("serviceCode", None)
    phone_number = request.values.get("phoneNumber", None)
    text = request.values.get("text", "").strip()

    # Normalize the phone number
    phone_number = normalize_phone_number(phone_number)

    logging.info(f"USSD Request: phone_number='{phone_number}', text='{text}'")

    if text == "":
        text = "CON Welcome to our SACCO \n"
        text += "1. Login \n"
        text += "2. No Account? \n"

    elif text == "1":
        registered_user = Tests.query.filter_by(phone_number=phone_number).first()
        if registered_user:
            text = "CON Please enter your PIN:"
        else:
            text = "END This phone number is not registered. Please register or try again."

    elif text.startswith("1*") or (text.isdigit() and len(text) > 1):
        pin = text.split('*')[1].strip() if text.startswith("1*") else text.strip()

        registered_user = Tests.query.filter_by(phone_number=phone_number).first()
        
        if registered_user:
            logging.info(f"Stored Hash: {registered_user.pin}, Entered PIN: '{pin}'")

            if registered_user.verify_pin(pin):  # Using the model's verify_pin method
                text = "CON Login successful! Choose an option: \n"
                text += "1. Withdrawals \n"
                text += "2. Deposits \n"
                text += "3. Account Management \n"
                text += "4. Enquiries \n"
                text += "0. Exit \n"
            else:
                logging.error(f"Invalid PIN for user {phone_number}. Entered PIN: '{pin}', Stored Hash: '{registered_user.pin}'")
                text = "END Invalid PIN. Please try again."
        else:
            text = "END User not found. Please register first."

    elif text == "2":
        text = "CON Enter your phone number:"

    elif text.startswith("2*"):
        parts = text.split('*')
        if len(parts) == 2:
            phone_number = parts[1].strip()
            text = "CON Please enter your National ID number:"
        elif len(parts) == 3:
            national_id = parts[2].strip()
            text = "CON Please enter your PIN:"
        elif len(parts) == 4:
            phone_number = parts[1].strip()
            national_id = parts[2].strip()
            pin = parts[3].strip()

            logging.info(f"Registering user: phone_number='{phone_number}', national_id='{national_id}', pin='{pin}'")
            registration_message = register_user(phone_number, national_id, pin)
            text = f"END {registration_message['message'] if 'message' in registration_message else registration_message}"

    elif text == "0":
        text = "END Thank you for using our SACCO services."

    elif text == "1*1":
        # Withdrawals
        text = "CON Withdraw from: \n"
        text += "1. Savings \n"
        text += "2. Loan \n"
        
    elif text == "1*1*1" or text == "1*1*2":
        # Choose withdrawal type
        withdrawal_type = "savings" if text.endswith("*1") else "loan"
        text = "CON Withdraw to: \n"
        text += "1. Mobile Money \n"
        text += "2. M-Pesa \n"
        
    elif text == "1*1*1*1" or text == "1*1*1*2":
        # Enter amount to withdraw
        text = "CON Enter the amount you wish to withdraw:"
    elif text.startswith("1*1*1*1*") or text.startswith("1*1*1*2*"):
        amount = text.split('*')[-1]  # Get the amount
        withdrawal_type = "savings" if "1*1*1*1*" in text else "loan"
        text = f"END You have successfully withdrawn KES {amount} from your {withdrawal_type}."
        
    elif text == "1*2":
        text = "CON Deposit to: \n"
        text += "1. Loan Repayment \n"
        text += "2. Savings \n"
        text += "3. Shares \n"
        
    elif text.startswith("1*2*"):
        # Handle deposits
        deposit_type = ""
        if text == "1*2*1":
            deposit_type = "Loan Repayment"
        elif text == "1*2*2":
            deposit_type = "Savings"
        elif text == "1*2*3":
            deposit_type = "Shares"
        text = "CON Deposit via: \n"
        text += "1. M-Pesa \n"
        text += "2. Mobile Money \n"
        
    elif text.startswith("1*2*1*1") or text.startswith("1*2*1*2") or text.startswith("1*2*2*1") or text.startswith("1*2*2*2") or text.startswith("1*2*3*1") or text.startswith("1*2*3*2"):
        amount = text.split('*')[-1]
        if "1*2*1" in text:
            deposit_type = "Loan Repayment"
        elif "1*2*2" in text:
            deposit_type = "Savings"
        elif "1*2*3" in text:
            deposit_type = "Shares"
        text = f"END You have successfully deposited KES {amount} to {deposit_type}."
        
    elif text == "1*3":
        # Account Management
        text = "CON Account Management: \n"
        text += "1. Change PIN \n"
        text += "2. Request Statement & Balance \n"
        
    elif text == "1*3*1":
        # Change PIN
        text = "CON Enter your current PIN:"
    elif text.startswith("1*3*1*"):
        current_pin = text.split('*')[2]
        new_pin = text.split('*')[3]
        if current_pin in registered_user:  # Verify current PIN
            registered_user[new_pin] = registered_user.pop(current_pin)  # Change PIN in the data
            text = "END Your PIN has been changed successfully."
        else:
            text = "END Invalid current PIN."
    elif text == "1*3*2":
        # Request Statement & Balance
        pin = text.split('*')[2]
        if pin in registered_user:
            transactions = "\n".join(registered_user[pin]["transactions"])
            balance = registered_user[pin]["balance"]
            text = f"END Your last 5 transactions are:\n{transactions}\nYour balance is KES {balance}."
        else:
            text = "END Invalid PIN."
            
    elif text == "1*4":
        # Enquiries
        text = "CON Enquiries: \n"
        text += "1. FAQs \n"
        text += "2. Help \n"
        
    elif text == "1*4*1":
        # FAQs
        text = "END Frequently Asked Questions: \n"
        text += "1. How do I reset my PIN? \n"
        text += "2. How do I check my balance? \n"
        text += "3. What to do if I forget my PIN? \n"
        
    elif text == "1*4*2":
        # Help
        text = "END For assistance, contact customer support at 0712345678 or visit our website."

    resp = make_response(text, 200)
    resp.headers['Content-Type'] = "text/plain"
    return resp
