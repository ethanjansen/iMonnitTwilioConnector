# server.py
# By: Ethan Jansen
# Websocket server for iMonnit--sends text with Twilio. Requires Basic Authorization.

from flask import Flask, request
import logging
from functools import wraps
from settings import AppName, ImonnitTwilioConnectorConfig
from twilioClient import TwilioSMSClient
from dataTypes import Event, ValidationError
from db import DbConnector
import sys

# Register app
app = Flask(AppName)
twilioClient = TwilioSMSClient()
dbConnector = DbConnector()


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
    """
    Expected iMonnit Rule Webhook Contents:
    {
        subject: Subject/Title of Rule
        reading: Reading or event that triggered the Rule
        rule: Name of Rule (REQUIRED)
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

    # Log
    app.logger.info("iMonnit webhook POST received")

    data = request.json
    sendTwilio = twilioClient.recipientListLength > 0

    try:
        # parse/validate event data
        event = Event(**data)
        app.logger.info(f"Rule: {event.rule}")

        # send Twilio messages
        twilioReturn = None
        if sendTwilio:
            twilioReturn = twilioClient.send(event.messageBody)
            event.messages = twilioReturn.messages

            # check if twilio was able to send messages.
            # Note: if nothing could be sent when it should have,
            # nothing will be added to db and return status will inform client to retry later (hopefully)
            if twilioReturn.nothingSent:
                # all messages (if present) should have errors if nothingSent
                errorString = "Sending messages to recipients resulted in errors:"
                for msg in twilioReturn.messages:
                    errorString += f"\n{msg.errorMessage} {msg.errorCode}"
                return (errorString, 500)  # InternalServerError

        # add to db
        if not dbConnector.addEventWithMessages(event):
            return ("Unable to add event details to db", 500)  # InternalServerError

        # do nothing further if no sms recipients
        if not sendTwilio:
            app.logger.info("No SMS recipients")
            return ("", 200)  # OK

    # other exceptions handled by flask default handler
    except ValidationError as e:
        if sendTwilio:
            # These are not saved to db, nor checked for twilio errors
            twilioClient.send("Error: Received bad data from iMonnit Webhook!")
        app.logger.error(f"Received bad data from iMonnit Webhook: {e.errors()}")
        return ("Unexpected Data", 400)  # BadRequest

    # Return success -  atLEAST ONE sms was sent successfully and info added to db
    return ("", 200)  # OK


# Run
if __name__ == "__main__":
    app.logger.setLevel(logging.INFO)

    # test database connection
    if not dbConnector.testConnection():
        app.logger.critical("Unable to connect to database! Exiting...")
        sys.exit(2)

    # run app
    app.run(host="0.0.0.0", port=ImonnitTwilioConnectorConfig.ServerPort)
