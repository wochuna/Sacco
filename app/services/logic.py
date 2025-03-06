import logging
from flask import make_response
from app.models import Tests
from app.helpers.utils import normalize_phone_number, verify_pin, register_user, ussd_response, process_withdrawal

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
                    text += "4. Enquiries \n"
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


    elif text == "1*2":
        text = "CON Deposit to: \n"
        text += "1. Loan Repayment \n"
        text += "2. Savings \n"
        text += "3. Shares \n"

    elif text.startswith("1*2*"):
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
