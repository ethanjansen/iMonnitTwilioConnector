# webhook.py
# By: Ethan Jansen
# Webhooks for flask server.
# imonnit: Websocket server for iMonnit--sends text with Twilio. Requires Basic Authorization.

from datetime import datetime
from flask import Blueprint, request
import logging
from . import dbConn, smsClient
from .auth import login_required
from .dataTypes import Event, Message, ValidationError
from .twilioClient import TwilioErrorCodes


# create blueprint
bpName = "webhook"
webhookBp = Blueprint(bpName, __name__, url_prefix="/"+bpName)
logger = logging.getLogger(__name__)


# Routes
@webhookBp.post("/imonnit")
@login_required
def imonnit():
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
    logger.info("iMonnit webhook POST received")

    # iMonnit uses json
    data = request.json
    sendTwilio = smsClient.recipientListLength > 0

    try:
        # parse/validate event data
        event = Event(**data)
        logger.info(f"Rule: {event.rule}")

        # send Twilio messages
        twilioReturn = None
        if sendTwilio:
            twilioReturn = smsClient.send(event.messageBody)
            event.messages = twilioReturn.messages

            # check if twilio was able to send messages.
            # Note: if nothing could be sent when it should have,
            # nothing will be added to db and return status will inform client to retry later (hopefully)
            if twilioReturn.nothingSent:
                # all messages (if present) should have errors if nothingSent
                errorString = "Sending Twilio messages resulted in errors: "
                errorString += ", ".join([str(x.errorCode) for x in twilioReturn.messages])
                return (errorString, 500)  # InternalServerError

        # add to db
        if not dbConn.addEventWithMessages(event):
            return ("Unable to add event details to db", 500)  # InternalServerError

        # do nothing further if no sms recipients
        if not sendTwilio:
            logger.info("No SMS recipients")
            return ("", 200)  # OK

    # other exceptions handled by flask default handler
    except ValidationError as e:
        if sendTwilio:
            # These are not saved to db, nor checked for twilio errors
            smsClient.send("Error: Received bad data from iMonnit Webhook!")
        logger.error(f"Received bad data from iMonnit Webhook: {e.errors()}")
        return ("Unexpected Data", 400)  # BadRequest

    # Return success -  atLEAST ONE sms was sent successfully and info added to db
    return ("", 200)  # OK


@webhookBp.post("/twilio")
@login_required
def twilio():
    """
    Expected Twilio SMS Status callback data:
    {
        MessageSid: message id (Message.messageId)
        From: the phone number that sent the message
        To: the phone number of the recipient (Message.recipient)
        Body: text body of the message: Up to 1600 characters
        MessageStatus: status of the message resource at the time the status callback was sent (Message.status)
        ErrorCode: if an error occured (MessageStatus is failed or undelivered), additional information (Message.errorCode)
        RawDlrDoneDate: The done date included in the delivery receipt (MessageStatus is delivered) (Message.deliveredDT)
    }

    Might need to add additional information:
    {
        Message.sentDT: DT for MessageStatus == sent
        Messge.errorMessage: Twilio error message associated with ErrorCode
        Message.updated: DT webhook was received
    }
    """

    # Log
    logger.info("Twilio webhook POST received")

    # Twilio uses x-www-form-urlencoded
    data = request.form.to_dict()

    try:
        # get addtional info if necessary
        sentDT = None
        errorMessage = None
        if data.get("MessageStatus") == "sent":
            # UTC
            sentDT = datetime.now()
        if "ErrorCode" in data:
            errorMessage = TwilioErrorCodes.getError(data["ErrorCode"])

        # receive message details
        msg = Message(messageId=data.get("MessageSid"),
                      recipient=data.get("To"),
                      status=data.get("MessageStatus"),
                      sentDT=sentDT,
                      deliveredDT=data.get("RawDlrDoneDate"),
                      errorCode=data.get("ErrorCode"),
                      errorMessage=errorMessage,
                      updated=datetime.now())
        logger.info(f"Message: {msg.messageId}")

        # update db
        if not dbConn.updateMessage(msg):
            return ("Unable to update db with message callback", 500)  # InternalServerError
    except ValidationError as e:
        # This is not logged to db
        logger.error(f"Received bad data from Twilio Webhook: {e.errors()}")
        return ("Unexpected Data", 400)  # BadRequest

    # Return success
    return ("", 200)
