from twilio.request_validator import RequestValidator
import os

validator = RequestValidator(os.environ["TWILIO_AUTH_TOKEN"])

@app.route("/webhook/sms", methods=["POST"])
def sms_webhook():
    # Validate Twilio signature
    sig = request.headers.get("X-Twilio-Signature", "")
    url = request.url
    params = request.form.to_dict()
    if not validator.validate(url, params, sig):
        return "Invalid signature", 403

    message_sid = request.form.get("MessageSid", "")
    if already_logged(message_sid):          # idempotency check
        return str(MessagingResponse())

    try:
        handle_incoming_sms(request.form.get("From", "Unknown"),
                            request.form.get("Body", ""))
    except Exception:
        app.logger.exception("Failed to process SMS")
    return str(MessagingResponse())
