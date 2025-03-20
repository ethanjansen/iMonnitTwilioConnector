# server.py
# By: Ethan Jansen
# Websocket server for iMonnit--sends text with Twilio. Requires Basic Authorization.

from flask import Flask, request, jsonify
from werkzeug.exceptions import ServiceUnavailable, InternalServerError, BadRequest
import logging
from functools import wraps
from settings import AppName, ImonnitTwilioConnectorConfig
from twilioClient import TwilioSMSClient

# Register app
app = Flask(AppName)
twilioClient = TwilioSMSClient()


# Helper functions
# Authentication check
def checkAuth(username, password):
    userCheck = username == ImonnitTwilioConnectorConfig.WebhookUser
    passCheck = password == ImonnitTwilioConnectorConfig.WebhookPassword

    return userCheck and passCheck


# Authentication wrapper
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not (auth and checkAuth(auth.username, auth.password)):
            return ("Unauthorized", 401, {"WWW-Authenticate": 'Basic realm="Login Required"'})

        return f(*args, **kwargs)
    return decorated_function


# Routes
@app.post("/webhook")
@login_required
def webhook():
    # Log
    app.logger.info(f"Data received: {request.json}")

    """
    Expected iMonnit Rule Webhook Contents:
    {
        subject: Subject/Title of Rule
        reading: Reading or event that triggered the Rule
        rule: Name of Rule
        date: Date the rule triggered
        time: Time the rule triggered
        readingDate: Date of data message (if rule triggered by sensor reading)
        readingTime: Time of data message (if rule triggered by sensor reading)
        originalReadingDate: Date of first data message that triggered the rule (if rule triggered by sensor reading)
        originalReadingTime: Time of first data message that triggered the rule (if rule triggered by sensor reading)
        acknowledgeURL: URL that will acknowledge the rule if called (Log in requried)
        parentAccount: Name of the reseller or immediate parent in corporate hierarchy
        deviceID: The iD of the device that triggered the rule
        name: Name of the device that triggered the rule
        networkID: The ID of the network that the device triggerd the rule belongs to
        network: Network that the device triggering the rule belongs to
        accountID: The ID of the account the rule belongs to
        accountNumber: Account number of the account the rule belongs to
        companyName: Company name of the account the rule belongs to
    }
    """
    data = request.json

    # Optionally add to database [TODO]

    # If there are no sms recipients, do nothing
    if twilioClient.recipientListLength == 0:
        app.logger.info("No SMS Recipients")
        return ("", 200)

    # Send stuff with Twilio
    body = "Error: Received bad data from iMonnit Webhook!"
    if "rule" in data:
        rule = data["rule"]
        name = data.get("name", "name")
        deviceID = data.get("deviceID", "deviceID")
        time = data.get("time", "time")
        date = data.get("date", "date")
        reading = data.get("reading", "reading")
        ack = data.get("acknowledgeURL", "acknowledgeURL")

        body = f"""{rule} triggered by {name} ({deviceID})
Time: {time} {date}
Reading: {reading}
Acknowledge: {ack}"""
    else:
        twilioClient.send(body)
        app.logger.warning("Received bad data from iMonnit Webhook")
        raise BadRequest(description="Unexpected data")

    results = twilioClient.send(body)

    if len(results) == twilioClient.recipientListLength:
        # Nothing was sent - likely throttled
        raise ServiceUnavailable(description="\n".join(f"Recipient={x[0]}, Error={x[1]} {x[2]}" for x in results))

    # Return success - This atLEAST ONE sms was sent successfully
    return ("Success", 200)


# Run
if __name__ == "__main__":
    app.logger.setLevel(logging.INFO)
    app.run(host="0.0.0.0", port=ImonnitTwilioConnectorConfig.ServerPort)
