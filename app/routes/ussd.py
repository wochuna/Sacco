from flask import Flask, request, Blueprint, make_response

# Initialize africastalking
# Africastalking.initialize
ussd_bp = Blueprint('ussd', __name__)
app = Flask(__name__)
@ussd_bp.route('/api/ussd/callback', methods=['POST', 'GET'])
def ussd_callbacks():
    session_id = request.values.get("sessionId", None)
    service_code = request.values.get("serviceCode", None)
    phone_number = request.values.get("phoneNumber", None)
    text = request.values.get("text", "")

    if text == "":
        text = "CON Welcome to SACCO \n"
        text += "1. Login \n"
        text += "2. No Account? \n"

    elif text == "1":
        text = "CON Please enter your PIN:"

    elif "1*" in text:
        pin = text.split('*')[1]
        # Here you would typically verify the PIN (not implemented in this example)
        text = "CON Login successful! Choose an option: \n"
        text += "1. Withdrawals \n"
        text += "2. Deposits \n"
        text += "3. Account Management \n"
        text += "4. Enquiries \n"
        text += "0. Exit \n"

    elif text == "2":
        text = "END Please visit your SACCO administrator for assistance."

    elif text == "0":
        text = "END Thank you for using SACCO services."
   
    elif text == "1*1":
        # Withdrawals
        text = "CON Withdraw from: \n"
        text += "1. Savings \n"
        text += "2. Loan \n"

    

    elif text == "1*1*1" or text == "1*1*2":
        # Choose withdrawal type
        withdrawal_type = "savings" if text.endswith("*1") else "loan"
        text = f"CON Withdraw to: \n"
        text += "1. Mobile Money \n"
        text += "2. M-Pesa \n"

    elif text == "1*1*1*1" or text == "1*1*1*2":
        # Enter amount to withdraw
        text = "CON Enter the amount you wish to withdraw:"

    elif text.startswith("1*1*1*1*") or text.startswith("1*1*1*2*"):
        amount = text.split('*')[-1]  # Get the amount
        text = f"END You have successfully withdrawn KES {amount} from your {withdrawal_type}."
        
        
    elif text == "1*2":
        text = "CON Deposit to:"
        
    elif text == "1*2*1" or text == "1*2*2" or text == "1*2*3":
        # Choose deposit type
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

    elif text == "1*2*1*1" or text == "1*2*1*2" or text == "1*2*2*1" or text == "1*2*2*2" or text == "1*2*3*1" or text == "1*2*3*2":
        # Enter amount to deposit
        text = "CON Enter the amount you wish to deposit:"

    elif text.startswith("1*2*1*1*") or text.startswith("1*2*1*2*") or text.startswith("1*2*2*1*") or text.startswith("1*2*2*2*") or text.startswith("1*2*3*1*") or text.startswith("1*2*3*2*"):
        amount = text.split('*')[-1]  # Get the amount
        deposit_type = ""
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
    if current_pin in user_data:  # Verify current PIN
            user_data[new_pin] = user_data.pop(current_pin)  # Change PIN in the data
            text = "END Your PIN has been changed successfully."
    else:
            text = "END Invalid current PIN."

    elif text == "1*3*2":
        # Request Statement & Balance
        pin = text.split('*')[2]
    if pin in user_data:
            transactions = "\n".join(user_data[pin]["transactions"])
            balance = user_data[pin]["balance"]
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
        text = "END For assistance, contact customer support at 123-456-7890 or visit our website."
    
    resp = make_response(text, 200)
    resp.headers['Content-Type'] = "text/plain"
    return resp   

if __name__ == "__main__":
        app.run()
        
        
        
        
        
        
        
        
        
        
   