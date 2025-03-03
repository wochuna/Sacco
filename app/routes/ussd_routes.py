from app.services.logic import handle_ussd_request
from flask import Blueprint, request


ussd_bp = Blueprint('ussd', __name__)

@ussd_bp.route('/ussd/callback', methods=['POST', 'GET'])
def ussd():
    """USSD route to handle incoming USSD requests."""
    session_id = request.form.get("sessionId", "")
    service_code = request.form.get("serviceCode", "")
    phone_number = request.form.get("phoneNumber", "")
    text = request.form.get("text", "")

    return handle_ussd_request(session_id, service_code, phone_number, text)
