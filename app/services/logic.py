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
    validate_pin,
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
        "#": "main",  # Back to main menu
    },
    "withdrawals": {
        "1": "sacco_to_savings",
        "2": "sacco_to_mobile",
        "3": "savings_to_sacco",
        "4": "savings_to_mobile",
        "#": "logged_in",  # Back 
    },
    "sacco_to_mobile": {
        "1": "mpesa_sacco",
        "2": "airtel_sacco",
        "#": "withdrawals",  # Back 
    },
    "savings_to_mobile": {
        "1": "mpesa_savings",
        "2": "airtel_savings",
        "#": "withdrawals",  # Back 
    },
    "deposits": {
        "1": "mobile_money_deposit",
        "2": "sacco_wallet_deposit",
        "#": "logged_in",  # Back 
    },
    "mobile_money_deposit": {
        "1": "mobile_to_sacco",
        "2": "mobile_to_savings",
        "#": "deposits",  # Back
    },
    "mobile_to_sacco": {
        "1": "mpesa_to_sacco",
        "2": "airtel_to_sacco",
        "#": "mobile_money_deposit",  # Back 
    },
    "mobile_to_savings": {
        "1": "mpesa_to_savings",
        "2": "airtel_to_savings",
        "#": "mobile_money_deposit",  # Back 
    },
    "account_management": {
        "1": "update_pin",
        "2": "view_account_details",
        "#": "logged_in",  # Back 
    },
    "loans": {
        "1": "apply_loan",
        "2": "loan_status",
        "#": "logged_in",  # Back 
    },
    "enquiries": {
        "1": "mini_statement",
        "2": "faqs",
        "3": "help",
        "#": "logged_in",  # Back 
    },
    "faqs": {
        "1": "faq_balance",
        "2": "faq_loan",
        "3": "faq_pin",
        "4": "faq_support",
        "#": "enquiries",  # Back 
    },
    "register": {
        "phone": "enter_phone",
        "national_id": "enter_national_id",
        "pin": "enter_pin_register",
    },
}

# map menus that require input processing
INPUT_PROCESSING_MENUS = {
    "sacco_to_savings": "process_sacco_to_savings",
    "savings_to_sacco": "process_savings_to_sacco",
    "sacco_wallet_deposit": "process_sacco_wallet_deposit",
    "mpesa_sacco": "process_mobile_number",
    "airtel_sacco": "process_mobile_number",
    "mpesa_savings": "process_mobile_number",
    "airtel_savings": "process_mobile_number",
    "mpesa_to_sacco": "process_mobile_number",
    "airtel_to_sacco": "process_mobile_number", 
    "mpesa_to_savings": "process_mobile_number",
    "airtel_to_savings": "process_mobile_number",
    "update_pin": "process_current_pin",
    "new_pin": "process_new_pin",
    "confirm_new_pin": "process_confirm_pin",
    "view_account_details": "process_view_details",
    "mini_statement": "process_mini_statement",
}

# parent menu mapping
PARENT_MENUS = {
    "withdrawals": "logged_in",
    "deposits": "logged_in",
    "account_management": "logged_in",
    "loans": "logged_in",
    "enquiries": "logged_in",
    "sacco_to_mobile": "withdrawals",
    "savings_to_mobile": "withdrawals",
    "mobile_money_deposit": "deposits",
    "mobile_to_sacco": "mobile_money_deposit",
    "mobile_to_savings": "mobile_money_deposit",
    "faqs": "enquiries",
}

# menu text templates
MENU_TEXT = {
    "main": "CON Welcome to our SACCO \n1. Login \n2. Register",
    "logged_in": "CON Choose an option: \n1. Withdrawals \n2. Deposits \n3. Account Management \n4. Loans \n5. Enquiries \n0. Exit \n#. Back to Main",
    "withdrawals": "CON Withdrawal from:\n1. Sacco To Savings \n2. Sacco To Mobile \n3. Savings To Sacco \n4. Savings To Mobile \n#. Back",
    "sacco_to_mobile": "CON Choose Mobile Money Provider:\n1. Mpesa Sacco \n2. Airtel Sacco \n#. Back",
    "savings_to_mobile": "CON Choose Mobile Money Provider:\n1. Mpesa Savings \n2. Airtel Savings \n#. Back",
    "deposits": "CON Choose deposit from:\n1. Mobile Money Deposit \n2. Sacco Wallet Deposit \n#. Back",
    "mobile_money_deposit": "CON Choose deposit destination:\n1. Mobile To Sacco \n2. Mobile To Savings \n#. Back",
    "mobile_to_sacco": "CON Choose Mobile Money Provider:\n1. Mpesa To Sacco \n2. Airtel To Sacco \n#. Back",
    "mobile_to_savings": "CON Choose Mobile Money Provider:\n1. Mpesa To Savings \n2. Airtel To Savings \n#. Back",
    "account_management": "CON Account Management:\n1. Update Pin \n2. View Account Details \n#. Back",
    "loans": "CON Choose an option for Loans:\n1. Apply Loan \n2. Loan Status \n#. Back",
    "enquiries": "CON Choose an enquiry option:\n1. Mini Statement \n2. Faqs \n3. Help \n#. Back",
    "faqs": "CON FAQs:\n1. Faq Balance \n2. Faq Loan \n3. Faq Pin \n4. Faq Support \n#. Back",
}

# store sessions with navigation history
sessions = {}

def get_menu_text(menu_name):
    """return the predefined menu text or generate it dynamically if not found"""
    if menu_name in MENU_TEXT:
        return MENU_TEXT[menu_name]
    else:
        # generate menu text dynamically if not in predefined templates
        if menu_name in MENU_MAP:
            text = f"CON {menu_name.replace('_', ' ').title()}:\n"
            for key, value in MENU_MAP[menu_name].items():
                text += f"{key}. {value.replace('_', ' ').title()} \n"
            return text
        return f"CON {menu_name.replace('_', ' ').title()}"

def handle_login(phone_number, choice, session_data, session_id, service_code):
    """handles the login process."""
    if "*" in choice:
        parts = choice.split("*")
        if len(parts) == 2:
            pin = parts[1]
        else:
            return ussd_response("END Invalid input.")
    else:
        pin = choice

    registered_user = Tests.query.filter_by(phone_number=phone_number).first()
    if registered_user and verify_pin(registered_user, pin):
        session_data["current_menu"] = "logged_in"
        session_data["menu_stack"].append("login")
        session_data["logged_in"] = True
        session_data["user_id"] = registered_user.id
        return ussd_response(get_menu_text("logged_in"))
    else:
        return ussd_response("END Invalid PIN. Please try again.")

def handle_registration(phone_number, choice, session_data):
    """handles the registration process."""
    if session_data["current_menu"] == "register" and "phone" in MENU_MAP["register"]:
        session_data["menu_stack"].append("register")
        session_data["current_menu"] = "enter_national_id"
        if validate_phone_number(choice):
            session_data["menu_stack"].append(choice)
            session_data["registration_phone"] = choice # Store phone
            return ussd_response("CON Please enter your National ID number:")
        else:
            return ussd_response("END Invalid phone number")

    elif session_data["current_menu"] == "enter_national_id":
        session_data["menu_stack"].append("enter_national_id")
        if validate_national_id(choice):
            session_data["menu_stack"].append(choice)
            session_data["registration_id"] = choice # Store ID
            session_data["current_menu"] = "enter_pin_register"
            return ussd_response("CON Please enter your PIN:")
        else:
            return ussd_response("END Invalid national ID")

    elif session_data["current_menu"] == "enter_pin_register":
        national_id = session_data.get["registration_id"] # Get stored ID
        registration_phone = session_data.get("registration_phone") # Get stored phone
        pin = choice
        registration_message = register_user(phone_number, national_id, pin)
        return ussd_response(f"END {registration_message['message'] if 'message' in registration_message else registration_message}")

def process_input(phone_number, menu_type, choice, session_data):
    """process input for specific menu types"""
    menu_stack = session_data["menu_stack"]
    
    # handle withdrawal from sacco to savings
    if menu_type == "process_sacco_to_savings":
        amount = choice
        session_data["temp_amount"] = amount
        session_data["temp_action"] = "sacco_to_savings"
        session_data["current_menu"] = "enter_pin_for_transaction"
        return ussd_response("CON Enter your PIN to confirm withdrawal:")
    
    # handle withdrawal from savings to sacco
    elif menu_type == "process_savings_to_sacco":
        amount = choice
        session_data["temp_amount"] = amount
        session_data["temp_action"] = "savings_to_sacco"
        session_data["current_menu"] = "enter_pin_for_transaction"
        return ussd_response("CON Enter your PIN to confirm withdrawal:")
    
    # handle PIN entry for transactions
    elif session_data["current_menu"] == "enter_pin_for_transaction":
        pin = choice
        session_data["pin"] = pin
        registered_user = Tests.query.filter_by(phone_number=phone_number).first()
        
        if registered_user and verify_pin(registered_user, pin):
            action = session_data.get("temp_action", "")
            amount = session_data.get("temp_amount", "0")
            
            if action == "sacco_to_savings":
                withdrawal_result = process_withdrawal(registered_user, float(amount), pin, "savings", "sacco_wallet")
                return ussd_response(f"END {withdrawal_result['message']}")
            elif action == "savings_to_sacco":
                withdrawal_result = process_withdrawal(registered_user, float(amount), pin, "sacco_wallet", "savings")
                return ussd_response(f"END {withdrawal_result['message']}")
            else:
                return ussd_response("END Unknown transaction type.")
        else:
            return ussd_response("END Invalid PIN. Please try again.")
    
    # process mobile number input for various mobile money services
    elif menu_type == "process_mobile_number":
        mobile_number = choice
        current_menu = session_data["current_menu"]
        session_data["temp_mobile"] = mobile_number
        
        # store original menu for later reference
        session_data["last_menu"] = current_menu
        
        # set next menu based on the current
        if current_menu in ["mpesa_sacco", "airtel_sacco", "mpesa_savings", "airtel_savings"]:
            return ussd_response("CON Enter amount to withdraw:")
        elif current_menu in ["mpesa_to_sacco", "airtel_to_sacco", "mpesa_to_savings", "airtel_to_savings"]:
            return ussd_response("CON Enter deposit amount:")
        else:
            return ussd_response("END Invalid menu state.")
    
    # handle direct sacco wallet deposit
    elif menu_type == "process_sacco_wallet_deposit":
        amount = choice
        deposit_result = process_deposit(phone_number, amount, "SACCO Wallet", "SACCO Wallet")
        return ussd_response(f"END {deposit_result['message']}")

    # process amount input after mobile number was provided
    elif session_data.get("temp_mobile") and session_data.get("last_menu"):
        amount = choice
        mobile_number = session_data.get("temp_mobile")
        last_menu = session_data.get("last_menu")
        
        # handle withdrawal to mobile money
        if last_menu in ["mpesa_sacco", "airtel_sacco"]:
            # Determine provider
            provider = "M-Pesa" if "mpesa" in last_menu else "Airtel Money"
            # get PIN or ask for PIN
            session_data["temp_amount"] = amount
            session_data["temp_provider"] = provider
            session_data["temp_action"] = "sacco_to_mobile"
            session_data["current_menu"] = "enter_pin_for_transaction"
            return ussd_response("CON Enter your PIN to confirm withdrawal:")
            
        # handle withdrawal to mobile money from savings
        elif last_menu in ["mpesa_savings", "airtel_savings"]:
            provider = "M-Pesa" if "mpesa" in last_menu else "Airtel Money"
            session_data["temp_amount"] = amount
            session_data["temp_provider"] = provider
            session_data["temp_action"] = "savings_to_mobile"
            session_data["current_menu"] = "enter_pin_for_transaction"
            return ussd_response("CON Enter your PIN to confirm withdrawal:")
            
        # handle deposit from mobile money to sacco
        elif last_menu in ["mpesa_to_sacco", "airtel_to_sacco"]:
            provider = "M-Pesa" if "mpesa" in last_menu else "Airtel Money"
            deposit_result = process_deposit(phone_number, amount, provider, "SACCO Wallet")
            return ussd_response(f"END {deposit_result['message']}")
            
        # handle deposit from mobile money to savings
        elif last_menu in ["mpesa_to_savings", "airtel_to_savings"]:
            provider = "M-Pesa" if "mpesa" in last_menu else "Airtel Money"
            deposit_result = process_deposit(phone_number, amount, provider, "Savings")
            return ussd_response(f"END {deposit_result['message']}")
    
    # handle current PIN entry for updating PIN
    elif menu_type == "process_current_pin":
        current_pin = choice
        registered_user = Tests.query.filter_by(phone_number=phone_number).first()
        if registered_user and verify_pin(registered_user, current_pin):
            session_data["menu_stack"].append(current_pin)
            session_data["current_menu"] = "new_pin"
            return ussd_response("CON Enter new PIN:")
        else:
            return ussd_response("END Invalid PIN. Please try again.")
    
    # handle new PIN entry
    elif menu_type == "process_new_pin":
        new_pin = choice
        session_data["menu_stack"].append(new_pin)
        session_data["current_menu"] = "confirm_new_pin"
        return ussd_response("CON Confirm new PIN:")
    
    # handle PIN confirmation
    elif menu_type == "process_confirm_pin":
        new_pin = session_data["menu_stack"][-1]
        confirm_pin = choice
        if new_pin == confirm_pin:
            registered_user = Tests.query.filter_by(phone_number=phone_number).first()
            change_user_pin(registered_user, new_pin)
            return ussd_response("END PIN changed successfully!")
        else:
            return ussd_response("END PINs do not match. Try again.")
    
    # handle view account details
    elif menu_type == "process_view_details":
        pin = choice
        registered_user = Tests.query.filter_by(phone_number=phone_number).first()
        if registered_user and verify_pin(registered_user, pin):
            return ussd_response(f"END Account Details:\nPhone: {registered_user.phone_number}\nnational_id: {registered_user.national_id}\n")
        else:
            return ussd_response("END Invalid PIN. Please try again.")
    
    # handle mini statement request
    elif menu_type == "process_mini_statement":
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
    
    return None

def handle_menu_navigation(current_menu, choice, phone_number, session_data):
    """handles navigation through menus based on user choices"""
    menu_stack = session_data["menu_stack"]
    
    # check for back navigation using #
    if choice == "#" and current_menu in MENU_MAP:
        parent_menu = MENU_MAP[current_menu].get("#")
        if parent_menu:
            session_data["current_menu"] = parent_menu
            # Don't add to stack when going back
            return ussd_response(get_menu_text(parent_menu))
    
    # check if user input is mapped to next menu
    next_menu = MENU_MAP.get(current_menu, {}).get(choice)
    
    if next_menu:
        # store current menu in stack before moving to next
        menu_stack.append(current_menu)
        session_data["current_menu"] = next_menu
        
        # special case for menus that need input rather than selection
        if next_menu == "sacco_to_savings":
            return ussd_response("CON Enter amount to withdraw:")
        elif next_menu in ["mpesa_sacco", "airtel_sacco", "mpesa_savings", "airtel_savings"]:
            return ussd_response("CON Enter your mobile number:")
        elif next_menu == "savings_to_sacco":
            return ussd_response("CON Enter amount to withdraw:")
        elif next_menu == "sacco_wallet_deposit":
            return ussd_response("CON Enter amount to deposit:")
        elif next_menu in ["mpesa_to_sacco", "airtel_to_sacco", "mpesa_to_savings", "airtel_to_savings"]:
            return ussd_response("CON Enter your mobile number:")
        elif next_menu == "update_pin":
            return ussd_response("CON Enter your current PIN:")
        elif next_menu == "view_account_details":
            return ussd_response("CON Enter your PIN to view account details:")
        elif next_menu == "mini_statement":
            return ussd_response("CON Enter your PIN to access Mini Statement:")
        elif next_menu in ["apply_loan", "loan_status"]:
            return ussd_response("END This feature is coming soon.")
        elif next_menu == "help":
            return ussd_response("END Please contact customer support via 0720000000.")
        elif next_menu in ["faq_balance", "faq_loan", "faq_pin", "faq_support"]:
            # FAQ responses
            faq_responses = {
                "faq_balance": "END To check balance, go to Enquiries > Mini Statement.",
                "faq_loan": "END To apply for a loan, navigate to Loans and follow the instructions.",
                "faq_pin": "END To reset PIN, contact customer support at 0720000000.",
                "faq_support": "END You can reach customer support via 0720000000."
            }
            return ussd_response(faq_responses.get(next_menu, "END Information not available."))
        # standard menus, display the menu text
        return ussd_response(get_menu_text(next_menu))
        
    return None

def handle_ussd_request(session_id, service_code, phone_number, text):
    """process USSD requests using a menu map with support for navigation."""
    phone_number = normalize_phone_number(phone_number)

    if not phone_number:
        logging.error("Invalid phone number format.")
        return ussd_response("END Error: Invalid phone number format.", 400)

    logging.info(f"USSD Request: phone_number='{phone_number}', text='{text}'")
    logging.info(f"Session ID: '{session_id}', Current Menu: '{sessions.get(session_id, {}).get('current_menu')}'")

    # initialize or retrieve session data
    if session_id not in sessions:
        sessions[session_id] = {
            "current_menu": "main",
            "menu_stack": [],
            "phone_number": phone_number,
            "logged_in": False
        }

    session_data = sessions[session_id]
    current_menu = session_data["current_menu"]

    # initial request - show main menu
    if text == "":
        logging.info("Initial request - showing main menu")
        session_data["current_menu"] = "main"
        session_data["menu_stack"] = []
        session_data["logged_in"] = False
        return ussd_response(get_menu_text("main"))

    # handle concatenated text
    processed_text = text
    if "*" in text and session_data["current_menu"] not in ["enter_national_id", "enter_pin_register"]:
        parts = text.split("*")
        processed_text = parts[-1]
        logging.info(f"Concatenated input detected. Parts: '{parts}', Processed text: '{processed_text}'")

    # handle special registration flow
    if text.startswith("2*"):
        parts = text.split("*")
        logging.info(f"Registration flow triggered with parts: '{parts}'")
        # registration with phone number
        if len(parts) == 2:
            phone_number_from_text = parts[1]
            logging.info(f"Two-part registration input. Phone: '{phone_number_from_text}'")
            if validate_phone_number(phone_number_from_text):
                session_data["menu_stack"].append("register")
                session_data["current_menu"] = "enter_national_id"
                session_data["registration_phone"] = phone_number_from_text  # Store phone
                return ussd_response("CON Please enter your National ID number:")
            else:
                return ussd_response("END Invalid phone number")
        # registration with phone number and national ID 
        elif len(parts) == 3:
            phone_number_from_text = parts[1]
            national_id = parts[2]
            logging.info(f"Three-part registration input. Phone: '{phone_number_from_text}', ID: '{national_id}'")
            if validate_phone_number(phone_number_from_text) and validate_national_id(national_id):
                session_data["menu_stack"].append("register")
                session_data["menu_stack"].append(phone_number_from_text)
                session_data["current_menu"] = "enter_pin_register"
                session_data["registration_phone"] = phone_number_from_text  # Store phone
                session_data["registration_id"] = national_id        # Store ID
                return ussd_response("CON Please enter your PIN:")
            else:
                return ussd_response("END Invalid phone number or national ID.")
        # registration complete with PIN
        elif len(parts) == 4:
            phone_number_from_text = parts[1]
            national_id = parts[2]
            pin = parts[3]
            logging.info(f"Four-part registration input. Phone: '{phone_number_from_text}', ID: '{national_id}', PIN: '{pin}'")
            if validate_phone_number(phone_number_from_text) and validate_national_id(national_id) and validate_pin(pin):
                registration_message = register_user(phone_number_from_text, national_id, pin) # Use extracted phone
                return ussd_response(f"END {registration_message['message'] if 'message' in registration_message else registration_message}")
            else:
                error_message = "Invalid phone number, national ID, or PIN."
                if not validate_phone_number(phone_number_from_text):
                    error_message = "Invalid phone number."
                elif not validate_national_id(national_id):
                    error_message = "Invalid national ID."
                elif not validate_pin(pin):
                    error_message = "Invalid PIN."
                return ussd_response(f"END {error_message}")

        return None # If the '2*' condition is met but doesn't fit the parts, exit this block

    # handle main menu choices
    if current_menu == "main":
        if processed_text == "1":
            session_data["current_menu"] = "login"
            return ussd_response("CON Please enter your PIN to proceed:")
        elif processed_text == "2":
            session_data["current_menu"] = "register"
            return ussd_response("CON Enter your phone number:")

    # handle login
    if current_menu == "login":
        return handle_login(phone_number, processed_text, session_data, session_id, service_code)

    # handle registration process
    elif current_menu == "register":
        if validate_phone_number(processed_text):
            session_data["menu_stack"].append("register")
            session_data["current_menu"] = "enter_national_id"
            session_data["registration_phone"] = processed_text
            return ussd_response("CON Please enter your National ID number:")
        else:
            return ussd_response("END Invalid phone number")
    elif current_menu == "enter_national_id":
        # Check if we received a three-part input
        if "*" in text and len(text.split("*")) == 3:
            parts = text.split("*")
            national_id = parts[2]
            if validate_national_id(national_id):
                session_data["registration_id"] = national_id
                session_data["current_menu"] = "enter_pin_register"
                return ussd_response("CON Please enter your PIN:")
            else:
                return ussd_response("END Invalid national ID")
        elif validate_national_id(processed_text):
            session_data["menu_stack"].append(processed_text)
            session_data["registration_id"] = processed_text
            session_data["current_menu"] = "enter_pin_register"
            return ussd_response("CON Please enter your PIN:")
        else:
            return ussd_response("END Invalid national ID")
    elif current_menu == "enter_pin_register":
        national_id = session_data.get("registration_id")
        registration_phone = session_data.get("registration_phone")
        pin = processed_text # Use processed_text for PIN
        registration_message = register_user(registration_phone, national_id, pin)
        return ussd_response(f"END {registration_message['message'] if 'message' in registration_message else registration_message}")

    # check if the current menu requires specific input processing
    if current_menu in INPUT_PROCESSING_MENUS:
        input_processor = INPUT_PROCESSING_MENUS[current_menu]
        result = process_input(phone_number, input_processor, processed_text, session_data)
        if result:
            return result

    # handle menu navigation for standard menu options
    nav_result = handle_menu_navigation(current_menu, processed_text, phone_number, session_data)
    if nav_result:
        return nav_result

    # process amount input after mobile number was provided (this also covers many other cases)
    if session_data.get("temp_mobile") and session_data.get("last_menu"):
        result = process_input(phone_number, "process_mobile_input", processed_text, session_data)
        if result:
            return result

    # if nothing matched but we're logged in, go back to logged_in menu
    if session_data.get("logged_in", False):
        session_data["current_menu"] = "logged_in"
        return ussd_response(get_menu_text("logged_in"))

    # if all else fails, return to main menu
    session_data["current_menu"] = "main"
    return ussd_response(get_menu_text("main"))

    resp = make_response(text, 200)
    resp.headers['Content-Type'] = "text/plain"
    return resp
