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
    text = request.values.get("text", "default")
    text = """CON What would you want to check?
    1. My Account \n
    2. My Phone Number \n
    3. My Branch
    """

    if text == "":
        text = "CON What would you want to check \n"
        text += "1. My Account \n"
        text += "2. My phone number \n"
        text += "3. My branch"

    elif text =="1":
        text = "CON Choose the account information that you want to view \n"
        text += "1. My Account balance\n"
        text += "2. My Account number \n"

    elif text =="2":
        text = "END Your phone number is "+phoneNumber

    elif text =="1*1":
        text = "END Your account number is ACOO10SWO2101."

    elif text =="1*2":
        text = "END Your BALANCE  is KES 120/-"

    resp = make_response(text, 200)
    resp.headers['Content-Type'] = "text/plain"
    return resp     

if __name__ == "__main__":
        app.run()
        