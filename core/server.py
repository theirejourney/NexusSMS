# core/server.py
from flask import Flask, request
from core.listener import handle_incoming_sms
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/webhook/sms", methods=["POST"])
def sms_webhook():
    sender = request.form.get("From", "Unknown")
    body = request.form.get("Body", "")
    
    handle_incoming_sms(sender, body)
    
    # Return an empty TwiML response to acknowledge receipt
    resp = MessagingResponse()
    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
