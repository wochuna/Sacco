import logging
from flask import make_response
from app.models import Tests, Withdrawals, Transactions
from app.helpers.utils import normalize_phone_number, verify_pin, register_user, ussd_response, process_withdrawal, process_deposit

def handle_ussd_request(session_id, service_code, phone_number, text):
    """Process USSD requests and return appropriate responses."""
    phone_number = normalize_phone_number(phone_number)

    if not phone_number:
        return ussd_response("END Error: Invalid phone number format.", 400)

    logging.info(f"USSD Request: phone_number='{phone_number}', text='{text}'")

    if text == "":
        text = "CON Welcome to our SACCO \n"
        text += "1. Login \n"
        text += "2. No Account? \n"

    elif text == "1":
        text = "CON Please enter your PIN to proceed:"

    elif text.startswith("1*") and len(text.split('*')) == 2:
        pin = text.split('*')[1]
        registered_user = Tests.query.filter_by(phone_number=phone_number).first()
        
        if registered_user and registered_user.verify_pin(pin):
            text = "CON Login successful! Choose an option: \n"
            text += "1. Withdrawals \n"
            text += "2. Deposits \n"
            text += "3. Account Management \n"
            text += "4. Loans \n"
            text += "5. Enquiries \n"
            text += "0. Exit \n"
        else:
            text = "END Invalid PIN. Please try again."

    elif text == "2":
        text = "CON Enter your phone number:"
    
    elif text.startswith("2*"):
        parts = text.split('*')
        if len(parts) == 2:
            text = "CON Please enter your National ID number:"
        elif len(parts) == 3:
            text = "CON Please enter your PIN:"
        elif len(parts) == 4:
            phone_number, national_id, pin = parts[1], parts[2], parts[3]
            registration_message = register_user(phone_number, national_id, pin)
            text = f"END {registration_message['message'] if 'message' in registration_message else registration_message}"

    elif text.startswith("1*") and len(text.split("*")) == 3:
        _, pin, option = text.split("*")
        registered_user = Tests.query.filter_by(phone_number=phone_number).first()

        if registered_user and registered_user.verify_pin(pin):
            if option == "1":  # Withdrawals
                text = "CON Select withdrawal option:\n1. To Savings\n2. To Mobile Money"
            elif option == "2":  # Deposits
                text = "CON Choose deposit method:\n1. Mobile Money\n2. SACCO Wallet"
            elif option == "3":  # Account Management
                text = "CON Account Management:\n1. Update PIN\n2. View Account Details"
            elif option == "4":  # Loans
                text = "CON Choose an option for Loans:\n1. Apply for a Loan\n2. Loan Status"
            elif option == "5":  # Enquiries
                text = "CON Choose an enquiry option:\n1. Mini Statement\n2. FAQs\n3. Help"
        else:
            text = "END Invalid PIN. Please try again."

    # Handle Withdrawals Flow
    elif text.startswith("1*") and len(text.split("*")) == 4:
        _, pin, option, sub_option = text.split("*")
        
        if option == "1" and sub_option == "1":
            text = "CON Enter amount to transfer to Savings:"
        elif option == "1" and sub_option == "2":
            text = "CON Select provider:\n1. M-Pesa\n2. Airtel Money"
        elif option == "2" and sub_option == "1":
            text = "CON Enter amount to transfer to Sacco Wallet:"
        elif option == "2" and sub_option == "2":
            text = "CON Select provider:\n1. M-Pesa\n2. Airtel Money"

    # Handle Deposits Flow
    elif text.startswith("2*") and len(text.split("*")) == 2:
        text = "CON Choose deposit method:\n1. Mobile Money\n2. SACCO Wallet"

    # Mobile Money submenu
    elif text.startswith("2*1"):
        text = "CON Choose deposit destination:\n1. SACCO Wallet\n2. Savings\n"

    # Choose mobile provider
    elif text in ["2*1*1", "2*1*2"]:
        destination = "SACCO Wallet" if text == "2*1*1" else "Savings"
        text = "CON Choose mobile provider:\n1. M-Pesa\n2. Airtel Money\n"

    elif text in ["2*1*1*1", "2*1*1*2", "2*1*2*1", "2*1*2*2"]:
        provider = "M-Pesa" if text.endswith("1") else "Airtel Money"
        text = "CON Enter your mobile number:"

    elif text.startswith("2*1*1*") or text.startswith("2*1*2*"):
        parts = text.split('*')
        if len(parts) == 5:
            text = "CON Enter deposit amount:"
        elif len(parts) == 6:
            text = "CON Enter your PIN to confirm transaction:"
        elif len(parts) == 7:
            provider = "M-Pesa" if parts[3] == "1" else "Airtel Money"
            destination = "SACCO Wallet" if parts[2] == "1" else "Savings"
            phone_number = parts[4]
            amount = parts[5]
            pin = parts[6]

            logging.info(f"Processing deposit: Provider={provider}, Destination={destination}, Phone={phone_number}, Amount={amount}")
            transaction_status = process_deposit(phone_number, amount, provider, destination)

            if transaction_status["status"]:
                text = f"END Deposit of KES {amount} from {provider} to {destination} is being processed."
            else:
                text = f"END Deposit failed: {transaction_status['message']}"

    # Account Management options
    elif text.startswith("1*3"):  # Account Management handling
        text = "CON Account Management:\n1. Update PIN\n2. View Account Details"

    elif text.startswith("3*"):
        parts = text.split('*')
        if len(parts) == 2:
            option = parts[1].strip()
            if option == "1":
                text = "CON Enter your current PIN:"
            elif option == "2":
                text = "CON Enter your PIN to view account details:"
            else:
                text = "END Invalid option. Please try again."
        elif len(parts) == 3:
            option = parts[1].strip()
            pin = parts[2].strip()
            registered_user = Tests.query.filter_by(phone_number=phone_number).first()

            if registered_user and registered_user.verify_pin(pin):
                if option == "1":
                    text = "CON Enter new PIN:"
                elif option == "2":
                    text = f"END Account Details:\nPhone: {registered_user.phone_number}\nnational_id: {registered_user.national_id}\n"
            else:
                text = "END Invalid PIN. Please try again."
        elif len(parts) == 4 and parts[1] == "1":
            new_pin = parts[3].strip()
            text = "CON Confirm new PIN:"
        elif len(parts) == 5 and parts[1] == "1":
            new_pin = parts[3].strip()
            confirm_pin = parts[4].strip()

            if new_pin == confirm_pin:
                registered_user.set_pin(new_pin)
                db.session.commit()
                text = "END PIN changed successfully!"
            else:
                text = "END PINs do not match. Try again."

    # Enquiries Menu
    elif text == "1*5":
        text = "CON Choose an enquiry option:\n1. Mini Statement\n2. FAQs\n3. Help"

    elif text.startswith("1*5*1"):  # Mini Statement
        text = "CON Enter your PIN to access Mini Statement:"

    elif text.startswith("1*5*1*"):
        user_pin = text.split("*")[-1]
        correct_pin = get_user_pin(phone_number)

        if user_pin == correct_pin:
            transactions = get_recent_transactions(phone_number, limit=5)
            if transactions:
                text = "END Last 5 Transactions:\n"
                for txn in transactions:
                    text += f"{txn['date']}: {txn['type']} {txn['amount']}\n"
            else:
                text = "END No recent transactions found."
        else:
            text = "END Incorrect PIN. Please try again."

    # FAQs Menu
    elif text == "1*5*2":
        text = "CON FAQs:\n1. How to check balance?\n2. How to apply for a loan?\n3. How to reset PIN?\n4. How to contact support?\n"

    # FAQs Answers
    elif text == "1*5*2*1":
        text = "END To check balance, go to Enquiries > Mini Statement."
    elif text == "1*5*2*2":
        text = "END To apply for a loan, navigate to Loans and follow the instructions."
    elif text == "1*5*2*3":
        text = "END To reset PIN, contact customer support at 0720000000."
    elif text == "1*5*2*4":
        text = "END You can reach customer support via 0720000000."

    # Help - Contact Support
    elif text == "1*5*3":
        text = "END Please contact customer support via 0720000000."

    resp = make_response(text, 200)
    resp.headers['Content-Type'] = "text/plain"
    return resp