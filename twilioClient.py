import logging
from settings import AppName, TwilioConfig
from twilio.base.exceptions import TwilioRestException
from twilio.http.http_client import TwilioHttpClient
from twilio.rest import Client as TwilioClient


class TwilioSMSClient:
    def __init__(self, logger=None, debug=TwilioConfig.Debug):
        # logging
        self._logger = logger
        if not self._logger:
            self._logger = logging.getLogger(AppName+"."+__name__)
        self._httpLog = logging.getLogger(self._logger.name+".httpclient")
        self._httpLog.setLevel(20 if debug else 30)

        # client config
        # expects TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables
        self._client = TwilioClient(http_client=TwilioHttpClient(logger=self._httpLog))

    # Get recipient list length
    @property
    def recipientListLength(self):
        return len(TwilioConfig.Recipients)

    # Default SMS sender
    # Arg: string message body.
    # Returns: list of (recipient, TwilioRestException.msg, TwilioRestException.status) for all exceptions occured. Empty list on complete success
    def send(self, body):
        returnList = []

        self._logger.info("Sending SMS with Twilio")
        # Send Loop
        for recipient in TwilioConfig.Recipients:
            try:
                msg = self._client.messages.create(
                    from_=TwilioConfig.PhoneSource,
                    to=recipient,
                    body=body,
                    )

                """
                to - message recipient
                date_created - when message created from app
                date_sent - when message sent from twilio (always None on app creation)
                sid - unique twilio message id
                status - status of message (queued, sending, sent, failed, delivered, undelivered, receiving, received)
                error_code - Error code if message status is failed or undeliverd, otherwise None
                error_message - Description of error_code, None if no error
                """
                self._logger.info(f"Successfully created message {msg.sid} to {msg.to} at {msg.date_created}. Status = {msg.status}")

            except TwilioRestException as e:
                self._logger.error(f"\"{e.msg}\" {e.status}")
                returnList.append((recipient, e.msg, e.status))

        if not returnList:
            self._logger.info("All SMS sent successfully")
        elif len(returnList) == self.recipientListLength:
            self._logger.warning("Unable to send anything with Twilio. Likely throttled.")

        return returnList


if __name__ == "__main__":
    # testing
    TestClient = TwilioSMSClient(debug=True)
    TestClient.send("Testing...")
