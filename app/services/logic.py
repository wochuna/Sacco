import logging
from flask import make_response
from app.models import Tests
from app.helpers.utils import (
    normalize_phone_number,
    register_user,
    ussd_response,
    process_withdrawal,
    process_deposit,
    validate_phone_number,
    validate_national_id,
    verify_pin,
    get_user_pin,
    get_recent_transactions,
    change_user_pin
)

MENU_MAP = {
    "main": {
        "1": "login",
        "2": "register",
    },
    "login": {
        "pin": "enter_pin",
    },
    "logged_in": {
        "1": "withdrawals",
        "2": "deposits",
        "3": "account_management",
        "4": "loans",
        "5": "enquiries",
        "0": "exit",
    },
    "withdrawals": {
        "1": "sacco_to_savings",
        "2": "sacco_to_mobile",
        "3": "savings_to_sacco",
        "4": "savings_to_mobile",
    },
    "sacco_to_mobile": {
        "1": "mpesa_sacco",
        "2": "airtel_sacco",
    },
    "savings_to_mobile": {
        "1": "mpesa_savings",
        "2": "airtel_savings",
    },
    "deposits": {
        "1": "mobile_money_deposit",
        "2": "sacco_wallet_deposit",
    },
    "mobile_money_deposit": {
        "1": "mobile_to_sacco",
        "2": "mobile_to_savings",
    },
    "mobile_to_sacco": {
        "1": "mpesa_to_sacco",
        "2": "airtel_to_sacco",
    },
    "mobile_to_savings": {
        "1": "mpesa_to_savings",
        "2": "airtel_to_savings",
    },
    "account_management": {
        "1": "update_pin",
        "2": "view_account_details",
    },
    "loans": {
        "1": "apply_loan",
        "2": "loan_status",
    },
    "enquiries": {
        "1": "mini_statement",
        "2": "faqs",
        "3": "help",
    },
    "faqs": {
        "1": "faq_balance",
        "2": "faq_loan",
        "3": "faq_pin",
        "4": "faq_support",
    },
    "register": {
        "phone": "enter_phone",
        "national_id": "enter_national_id",
        "pin": "enter_pin_register",
    },
}

def handle_login(phone_number, choice, menu_stack, session_id, service_code):
    """Handles the login process."""
    if "*" in choice:
        parts = choice.split("*")
        if len(parts) == 2:
            pin = parts[1]
        else:
            return ussd_response("END Invalid input.")
    else:
        return ussd_response("END Invalid input.")

    registered_user = Tests.query.filter_by(phone_number=phone_number).first()
    if registered_user and verify_pin(registered_user, pin):
        handle_ussd_request.current_menu = "logged_in"
        menu_stack.append("login")
        text = "CON Login successful! Choose an option: \n"
        for key, value in MENU_MAP["logged_in"].items():
            text += f"{key}. {value.replace('_', ' ').title()} \n"
        return ussd_response(text)
    else:
        return ussd_response("END Invalid PIN. Please try again.")

def handle_registration(phone_number, choice, menu_stack):
    """Handles the registration process."""
    if handle_ussd_request.current_menu == "register" and "phone" in MENU_MAP["register"]:
        menu_stack.append("register")
        handle_ussd_request.current_menu = "enter_national_id"
        if validate_phone_number(choice):
            menu_stack.append(choice)
            return ussd_response("CON Please enter your National ID number:")
        else:
            return ussd_response("END Invalid phone number")

    elif handle_ussd_request.current_menu == "enter_national_id":
        menu_stack.append("enter_national_id")
        if validate_national_id(choice):
            menu_stack.append(choice)
            handle_ussd_request.current_menu = "enter_pin_register"
            return ussd_response("CON Please enter your PIN:")
        else:
            return ussd_response("END Invalid national ID")

    elif handle_ussd_request.current_menu == "enter_pin_register":
        national_id = menu_stack[-2]
        pin = choice
        registration_message = register_user(phone_number, national_id, pin)
        return ussd_response(f"END {registration_message['message'] if 'message' in registration_message else registration_message}")


def handle_menu_options(current_menu, choice, phone_number, menu_stack, session_id, service_code):
    """Handles menu options based on the current menu."""
    if current_menu == "logged_in":
        if choice == "1":
            handle_ussd_request.current_menu = "withdrawals"
            text = "CON Withdrawal from:\n"
            for key, value in MENU_MAP["withdrawals"].items():
                text += f"{key}. {value.replace('_', ' ').title()} \n"
            return ussd_response(text)

        elif choice == "2":
            handle_ussd_request.current_menu = "deposits"
            text = "CON Choose deposit from:\n"
            for key, value in MENU_MAP["deposits"].items():
                text += f"{key}. {value.replace('_', ' ').title()} \n"
            return ussd_response(text)

        elif choice == "3":
            handle_ussd_request.current_menu = "account_management"
            text = "CON Account Management:\n"
            for key, value in MENU_MAP["account_management"].items():
                text += f"{key}. {value.replace('_', ' ').title()} \n"
            return ussd_response(text)

        elif choice == "4":
            handle_ussd_request.current_menu = "loans"
            text = "CON Choose an option for Loans:\n"
            for key, value in MENU_MAP["loans"].items():
                text += f"{key}. {value.replace('_', ' ').title()} \n"
            return ussd_response(text)

        elif choice == "5":
            handle_ussd_request.current_menu = "enquiries"
            text = "CON Choose an enquiry option:\n"
            for key, value in MENU_MAP["enquiries"].items():
                text += f"{key}. {value.replace('_', ' ').title()} \n"
            return ussd_response(text)

        elif choice == "0":
            return ussd_response("END Thank you for using our SACCO service!")
        else:
            return ussd_response("END Invalid choice.")


    elif current_menu == "withdrawals":
        text = "CON Withdrawal from:\n"
        for key, value in MENU_MAP["withdrawals"].items():
            text += f"{key}. {value.replace('_', ' ').title()} \n"
        return ussd_response(text)
    elif current_menu == "sacco_to_savings":
        return ussd_response("CON Enter amount to withdraw:")
    elif current_menu == "sacco_to_mobile":
        text = "CON Choose Mobile Money Provider:\n"
        for key, value in MENU_MAP["sacco_to_mobile"].items():
            text += f"{key}. {value.replace('_', ' ').title()} \n"
        return ussd_response(text)
    elif current_menu in ["mpesa_sacco", "airtel_sacco"]:
        return ussd_response("CON Enter your mobile number:")
    elif current_menu =="savings_to_sacco":
        return ussd_response("CON Enter amount to withdraw:")
    elif current_menu == "savings_to_mobile":
        text = "CON Choose Mobile Money Provider:\n"
        for key, value in MENU_MAP["savings_to_mobile"].items():
            text += f"{key}. {value.replace('_', ' ').title()} \n"
        return ussd_response(text)
    elif current_menu in ["mpesa_savings", "airtel_savings"]:
        return ussd_response("CON Enter your mobile number:")


    elif current_menu == "deposits":
        text = "CON Choose deposit from:\n"
        for key, value in MENU_MAP["deposits"].items():
            text += f"{key}. {value.replace('_', ' ').title()} \n"
        return ussd_response(text)
    elif current_menu == "mobile_money_deposit":
        text = "CON Choose deposit destination:\n"
        for key, value in MENU_MAP["mobile_money_deposit"].items():
            text += f"{key}. {value.replace('_', ' ').title()} \n"
        return ussd_response(text)
    elif current_menu == "mobile_to_sacco":
        text = "CON Choose Mobile Money Provider:\n"
        for key, value in MENU_MAP["mobile_to_sacco"].items():
            text += f"{key}. {value.replace('_', ' ').title()} \n"
        return ussd_response(text)
    elif current_menu in ["mpesa_to_sacco", "airtel_to_sacco"]:
        return ussd_response("CON Enter your mobile number:")
    elif current_menu == "mobile_to_savings":
        text = "CON Choose Mobile Money Provider:\n"
        for key, value in MENU_MAP["mobile_to_savings"].items():
            text += f"{key}. {value.replace('_', ' ').title()} \n"
        return ussd_response(text)
    elif current_menu in ["mpesa_to_savings", "airtel_to_savings"]:
        return ussd_response("CON Enter your mobile number:")
    elif current_menu == "sacco_wallet_deposit":
        return ussd_response("CON Enter amount to deposit:")


    elif current_menu == "account_management":
        text = "CON Account Management:\n"
        for key, value in MENU_MAP["account_management"].items():
            text += f"{key}. {value.replace('_', ' ').title()} \n"
        return ussd_response(text)
    elif current_menu == "update_pin":
        return ussd_response("CON Enter your current PIN:")
    elif current_menu == "view_account_details":
        return ussd_response("CON Enter your PIN to view account details:")
    elif current_menu == "loans":
        text = "CON Choose an option for Loans:\n"
        for key, value in MENU_MAP["loans"].items():
            text += f"{key}. {value.replace('_', ' ').title()} \n"
        return ussd_response(text)


    elif current_menu == "enquiries":
        text = "CON Choose an enquiry option:\n"
        for key, value in MENU_MAP["enquiries"].items():
            text += f"{key}. {value.replace('_', ' ').title()} \n"
        return ussd_response(text)


    elif current_menu == "faqs":
        text = "CON FAQs:\n"
        for key, value in MENU_MAP["faqs"].items():
            text += f"{key}. {value.replace('_', ' ').title()} \n"
        return ussd_response(text)


    elif current_menu == "exit":
        return ussd_response("END Thank you for using our SACCO service!")
    elif current_menu == "enter_phone":
        return ussd_response("CON Please enter your National ID number:")
    elif current_menu == "enter_national_id":
        return ussd_response("CON Please enter your PIN:")
    elif current_menu == "sacco_to_savings":
        amount = choice
        pin = menu_stack[-2]
        registered_user = Tests.query.filter_by(phone_number=phone_number).first()
        if registered_user and verify_pin(registered_user, pin):
            withdrawal_result = process_withdrawal(registered_user, float(amount), pin, "savings", "sacco_wallet")
            return ussd_response(f"END {withdrawal_result['message']}")
        else:
            return ussd_response("END Invalid PIN. Please try again.")
    elif current_menu in ["mpesa_sacco", "airtel_sacco"]:
        mobile_number = choice
        menu_stack.append(mobile_number)
        return ussd_response("CON Enter amount to withdraw:")
    elif current_menu == "savings_to_sacco":
        amount = choice
        pin = menu_stack[-2]
        registered_user = Tests.query.filter_by(phone_number=phone_number).first()
        if registered_user and verify_pin(registered_user, pin):
            withdrawal_result = process_withdrawal(registered_user, float(amount), pin, "sacco_wallet", "savings")
            return ussd_response(f"END {withdrawal_result['message']}")
        else:
            return ussd_response("END Invalid PIN. Please try again.")
    elif current_menu in ["mpesa_savings", "airtel_savings"]:
        mobile_number = choice
        menu_stack.append(mobile_number)
        return ussd_response("CON Enter amount to withdraw:")
    elif current_menu == "sacco_wallet_deposit":
        amount = choice
        deposit_result = process_deposit(phone_number, amount, "SACCO Wallet", "SACCO Wallet")
        return ussd_response(f"END {deposit_result['message']}")
    elif current_menu in ["mpesa_to_sacco", "airtel_to_sacco"]:
        mobile_number = choice
        menu_stack.append(mobile_number)
        return ussd_response("CON Enter deposit amount:")
    elif current_menu in ["mpesa_to_savings", "airtel_to_savings"]:
        mobile_number = choice
        menu_stack.append(mobile_number)
        return ussd_response("CON Enter deposit amount:")
    elif current_menu == "mobile_money_deposit" and menu_stack[-1] == "mobile_to_sacco":
        amount = choice
        mobile_number = menu_stack[-2]
        provider = "M-Pesa" if "mpesa_to_sacco" in menu_stack else "Airtel Money"
        deposit_result = process_deposit(phone_number, amount, provider, "SACCO Wallet")
        return ussd_response(f"END {deposit_result['message']}")
    elif current_menu == "mobile_money_deposit" and menu_stack[-1] == "mobile_to_savings":
        amount = choice
        mobile_number = menu_stack[-2]
        provider = "M-Pesa" if "mpesa_to_savings" in menu_stack else "Airtel Money"
        deposit_result = process_deposit(phone_number, amount, provider, "Savings")
        return ussd_response(f"END {deposit_result['message']}")


    elif current_menu == "update_pin":
        current_pin = choice
        registered_user = Tests.query.filter_by(phone_number=phone_number).first()
        if registered_user and verify_pin(registered_user, current_pin):
            menu_stack.append(current_pin)
            handle_ussd_request.current_menu = "new_pin"
            return ussd_response("CON Enter new PIN:")
        else:
            return ussd_response("END Invalid PIN. Please try again.")
    elif current_menu == "new_pin":
        new_pin = choice
        menu_stack.append(new_pin)
        handle_ussd_request.current_menu = "confirm_new_pin"
        return ussd_response("CON Confirm new PIN:")
    elif current_menu == "confirm_new_pin":
        new_pin = menu_stack[-1]
        confirm_pin = choice
        if new_pin == confirm_pin:
            registered_user = Tests.query.filter_by(phone_number=phone_number).first()
            change_user_pin(registered_user, new_pin)
            return ussd_response("END PIN changed successfully!")
        else:
            return ussd_response("END PINs do not match. Try again.")

    elif current_menu == "view_account_details":
        pin = choice
        registered_user = Tests.query.filter_by(phone_number=phone_number).first()
        if registered_user and verify_pin(registered_user, pin):
            return ussd_response(f"END Account Details:\nPhone: {registered_user.phone_number}\nnational_id: {registered_user.national_id}\n")
        else:
            return ussd_response("END Invalid PIN. Please try again.")
    elif current_menu == "enquiries" and choice == "1":
        menu_stack.append("enquiries")
        handle_ussd_request.current_menu = "mini_statement"
        return ussd_response("CON Enter your PIN to access Mini Statement:")
    elif current_menu == "mini_statement":
        user_pin = choice
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
        return ussd_response(text)

    elif current_menu == "enquiries" and choice == "2":
        handle_ussd_request.current_menu = "faqs"
        menu_stack.append("enquiries")
        text = "CON FAQs:\n"
        for key, value in MENU_MAP["faqs"].items():
            text += f"{key}. {value.replace('_', ' ').title()} \n"
        return ussd_response(text)
    elif current_menu == "faqs" and choice == "1":
        return ussd_response("END To check balance, go to Enquiries > Mini Statement.")
    elif current_menu == "faqs" and choice == "2":
        return ussd_response("END To apply for a loan, navigate to Loans and follow the instructions.")
    elif current_menu == "faqs" and choice == "3":
        return ussd_response("END To reset PIN, contact customer support at 0720000000.")
    elif current_menu == "faqs" and choice == "4":
        return ussd_response("END You can reach customer support via 0720000000.")
    elif current_menu == "enquiries" and choice == "3":
        return ussd_response("END Please contact customer support via 0720000000.")
    else:
        return None


def handle_ussd_request(session_id, service_code, phone_number, text):
    """Process USSD requests using a menu map."""
    phone_number = normalize_phone_number(phone_number)

    if not phone_number:
        return ussd_response("END Error: Invalid phone number format.", 400)

    logging.info(f"USSD Request: phone_number='{phone_number}', text='{text}'")

    if not hasattr(handle_ussd_request, "current_menu"):
        handle_ussd_request.current_menu = "main"
        handle_ussd_request.menu_stack = []

    current_menu = handle_ussd_request.current_menu
    menu_stack = handle_ussd_request.menu_stack

    if text == "":
        if handle_ussd_request.current_menu == "logged_in":
            return handle_menu_options(handle_ussd_request.current_menu, "", phone_number, handle_ussd_request.menu_stack, session_id, service_code)
        else:
            handle_ussd_request.current_menu = "main"
            handle_ussd_request.menu_stack.clear()
            text = "CON Welcome to our SACCO \n"
            for key, value in MENU_MAP["main"].items():
                text += f"{key}. {value.replace('_', ' ').title()} \n"
            return ussd_response(text)
    logging.info(f"Current Menu before concat check: {handle_ussd_request.current_menu}")
    if handle_ussd_request.current_menu == "logged_in":
        if "*" in text:
            parts = text.split("*")
            if len(parts) > 0 and parts[-1].isdigit():
                text = parts[-1]
                logging.info(f"Emulator fix: Extracted menu selection: {text}")
            else:
                logging.warning(f"Emulator fix: Invalid concatenated input: {text}")
                return ussd_response("END Invalid choice. Please enter a valid option number.")


    if handle_ussd_request.current_menu == "logged_in" and not text.isdigit():
        logging.warning(f"Unexpected input format in logged_in menu: {text}")
        return ussd_response("END Invalid choice. Please enter a valid option number.")

    if handle_ussd_request.current_menu in ["main", "register", "enter_national_id", "enter_pin_register"] and "*" in text:
        parts = text.split("*")
        if len(parts) == 2 and handle_ussd_request.current_menu in ["main", "register"]:
            choice = parts[0]
            phone_number_from_text = parts[1]
            logging.info(f"Extracted choice: {choice}, phone number: {phone_number_from_text}")
            if choice == "2" and validate_phone_number(phone_number_from_text):
                logging.info(f"Phone number validated: {phone_number_from_text}")
                menu_stack.append("register")
                handle_ussd_request.current_menu = "enter_national_id"
                menu_stack.append(phone_number_from_text)
                logging.info(f"Current Menu after concat check: {handle_ussd_request.current_menu}")
                return ussd_response("CON Please enter your National ID number:")
            else:
                logging.info(f"Phone number validation failed or choice not '2'.")
                return ussd_response("END Invalid input.")
        elif len(parts) == 3 and handle_ussd_request.current_menu == "enter_national_id":
            choice = parts[0]
            phone_number_from_text = parts[1]
            national_id = parts[2]
            logging.info(f"Extracted choice: {choice}, phone number: {phone_number_from_text}, national id: {national_id}")
            if choice == "2" and validate_phone_number(phone_number_from_text) and validate_national_id(national_id):
                logging.info(f"Phone number and national id validated")
                menu_stack.append("enter_national_id")
                handle_ussd_request.current_menu = "enter_pin_register"
                menu_stack.append(national_id)
                return ussd_response("CON Please enter your PIN:")
            else:
                logging.info("phone number or national id validation failed")
                return ussd_response("END Invalid input")
        elif len(parts) == 4 and handle_ussd_request.current_menu == "enter_pin_register":
            choice = parts[0]
            phone_number_from_text = parts[1]
            national_id = parts[2]
            pin = parts[3]
            logging.info(f"Extracted choice: {choice}, phone number: {phone_number_from_text}, national id: {national_id}, pin: {pin}")
            if choice == "2" and validate_phone_number(phone_number_from_text) and validate_national_id(national_id):
                logging.info(f"Phone number and national id validated")
                registration_message = register_user(phone_number, national_id, pin)
                return ussd_response(f"END {registration_message['message'] if 'message' in registration_message else registration_message}")
            else:
                logging.info(f"Phone number or national id validation failed or choice not '2'.")
                return ussd_response("END Invalid input.")
        else:
            logging.info("concatenated string, but not 2, 3 or 4 parts")
    logging.info(f"Concatenated check bypassed. Current Menu: {handle_ussd_request.current_menu}")

    choice = text
    next_menu = MENU_MAP.get(current_menu, {}).get(choice)

    if next_menu:
        menu_stack.append(current_menu)
        handle_ussd_request.current_menu = next_menu

        if next_menu == "login":
            return ussd_response("CON Please enter your PIN to proceed:")
        elif next_menu == "register":
            return ussd_response("CON Enter your phone number:")

    if current_menu == "login" and "pin" in MENU_MAP["login"]:
        return handle_login(phone_number, choice, menu_stack, session_id, service_code)
    elif current_menu in ["register", "enter_national_id", "enter_pin_register"]:
        return handle_registration(phone_number, choice, menu_stack)
    else:
        menu_response = handle_menu_options(current_menu, choice, phone_number, menu_stack, session_id, service_code)
        if menu_response:
            return menu_response

        if menu_stack:
            handle_ussd_request.current_menu = menu_stack.pop()
            return handle_ussd_request(session_id, service_code, phone_number, "")
        else:
            return ussd_response("END Invalid choice.")

    resp = make_response(text, 200)
    resp.headers['Content-Type'] = "text/plain"
    return resp
