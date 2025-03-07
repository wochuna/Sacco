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
    logging.info(f"Received USSD Request: text='{text}'")


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

    elif text.startswith("1*") and len(text.split('*')) == 2:
        try:
            pin = text.split('*', 1)[1].strip() if text.startswith("1*") else text.strip()

            registered_user = Tests.query.filter_by(phone_number=phone_number).first()

            if registered_user:
                is_valid  = registered_user.verify_pin(pin)
                logging.info(f"Pin verification result is: {is_valid}")
                if is_valid:
                    text = "CON Login successful! Choose an option: \n"
                    text += "1. Withdrawals \n"
                    text += "2. Deposits \n"
                    text += "3. Account Management \n"
                    text += "4. Loans \n"
                    text += "5. Enquiries \n"
                    text += "0. Exit \n"
                else:
                    logging.error(f"Invalid PIN for user {phone_number}. Entered PIN: '{pin}', Stored Hash: '{registered_user.pin}'")
                    text = "END Invalid PIN. Please try again."
            else:
                text = "END User not found. Please register first."
        except Exception as e:
            logging.error(f"Error processing PIN authentication: {str(e)}")
            text = "END An error occurred. Please try again later."

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

    # Withdrawals Flow
    elif text == "1*1":
        text = "CON Select withdrawal option:\n1. To Savings\n2. To Mobile Money"

    elif text == "1*1*1":
        text = "CON Enter amount to transfer to Savings:"

    elif text.startswith("1*1*1*"):
        amount = text.split("*")[-1]
        text = "CON Enter your PIN to confirm transfer to Savings:"

    elif text.startswith("1*1*1*" and len(text.split("*")) == 4):
        pin = text.split("*")[-1]
        result = process_withdrawal(phone_number, "sacco_wallet", "savings", amount, pin)
        text = f"END {result['message']}"

    elif text == "1*1*2":
        text = "CON Select provider:\n1. M-Pesa\n2. Airtel Money"

    elif text.startswith("1*1*2*") and len(text.split("*")) == 3:
        provider = "M-Pesa" if text.split("*")[-1] == "1" else "Airtel Money"
        text = "CON Enter phone number for mobile money withdrawal:"

    elif text.startswith("1*1*2*") and len(text.split("*")) == 4:
        phone = text.split("*")[-1]
        text = "CON Enter amount to withdraw to Mobile Money:"

    elif text.startswith("1*1*2*") and len(text.split("*")) == 5:
        amount = text.split("*")[-1]
        text = "CON Enter your PIN to confirm Mobile Money withdrawal:"

    elif text.startswith("1*1*2*") and len(text.split("*")) == 6:
        pin = text.split("*")[-1]
        result = process_withdrawal(phone_number, "sacco_wallet", provider, amount, pin, phone)
        text = f"END {result['message']}"

    elif text == "1*2":
        text = "CON Select withdrawal option:\n1. To Sacco Wallet\n2. To Mobile Money"

    elif text == "1*2*1":
        text = "CON Enter amount to transfer to Sacco Wallet:"

    elif text.startswith("1*2*1*"):
        amount = text.split("*")[-1]
        text = "CON Enter your PIN to confirm transfer to Sacco Wallet:"

    elif text.startswith("1*2*1*" and len(text.split("*")) == 4):
        pin = text.split("*")[-1]
        result = process_withdrawal(phone_number, "savings", "sacco_wallet", amount, pin)
        text = f"END {result['message']}"

    elif text == "1*2*2":
        text = "CON Select provider:\n1. M-Pesa\n2. Airtel Money"

    elif text.startswith("1*2*2*") and len(text.split("*")) == 3:
        provider = "M-Pesa" if text.split("*")[-1] == "1" else "Airtel Money"
        text = "CON Enter phone number for mobile money withdrawal:"

    elif text.startswith("1*2*2*") and len(text.split("*")) == 4:
        phone = text.split("*")[-1]
        text = "CON Enter amount to withdraw to Mobile Money:"

    elif text.startswith("1*2*2*") and len(text.split("*")) == 5:
        amount = text.split("*")[-1]
        text = "CON Enter your PIN to confirm Mobile Money withdrawal:"

    elif text.startswith("1*2*2*") and len(text.split("*")) == 6:
        pin = text.split("*")[-1]
        result = process_withdrawal(phone_number, "savings", provider, amount, pin, phone)
        text = f"END {result['message']}"

# Deposit main menu
    elif text == "2":
        text = "CON Choose deposit method:\n"
        text += "1. Mobile Money\n"
        text += "2. SACCO Wallet\n"

# Mobile Money submenu
    elif text == "2*1":
        text = "CON Choose deposit destination:\n"
        text += "1. SACCO Wallet\n"
        text += "2. Savings\n"

# Choose mobile provider
    elif text in ["2*1*1", "2*1*2"]:
        destination = "SACCO Wallet" if text == "2*1*1" else "Savings"
        text = "CON Choose mobile provider:\n"
        text += "1. M-Pesa\n"
        text += "2. Airtel Money\n"

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

# Deposit from SACCO Wallet to Savings
    elif text == "2*2":
        text = "CON Enter your SACCO Wallet number:"

    elif text.startswith("2*2*"):
        parts = text.split('*')
        if len(parts) == 3:
            text = "CON Enter deposit amount:"
        elif len(parts) == 4:
            text = "CON Enter your PIN to confirm transaction:"
        elif len(parts) == 5:
            wallet_number = parts[2]
            amount = parts[3]
            pin = parts[4]

            logging.info(f"Processing SACCO Wallet deposit: Wallet={wallet_number}, Amount={amount}")
            transaction_status = process_deposit(wallet_number, amount, "SACCO Wallet", "Savings")

            if transaction_status["status"]:
                text = f"END Deposit of KES {amount} from SACCO Wallet to Savings is being processed."
            else:
                text = f"END Deposit failed: {transaction_status['message']}"

    elif text == "1*3":
        text = "CON Account Management:\n"
        text += "1. Update PIN\n"
        text += "2. View Account Details\n"

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
    text = "CON Choose an enquiry option:\n"
    text += "1. Mini Statement\n"
    text += "2. FAQs\n"
    text += "3. Help\n"

# Mini Statement
elif text == "1*5*1":
    text = "CON Enter your PIN to access Mini Statement:"

# Mini Statement
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
    text = "CON FAQs:\n"
    text += "1. How to check balance?\n"
    text += "2. How to apply for a loan?\n"
    text += "3. How to reset PIN?\n"
    text += "4. How to contact support?\n"

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
