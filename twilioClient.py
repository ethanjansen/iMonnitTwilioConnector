# twilioClient.py
# By: Ethan Jansen
# Twilio Client

import logging
from settings import AppName, TwilioConfig
from dataTypes import Message
from pydantic import ValidationError
from typing import List, Tuple
from twilio.base.exceptions import TwilioRestException
from twilio.http.http_client import TwilioHttpClient
from twilio.rest import Client as TwilioClient


class TwilioSMSClient:
    class ClientReturn:
        def __init__(self, nothingSent: bool, messages: Message):
            self.nothingSent = nothingSent
            self.messages = messages

    def __init__(self, logger: str = None, debug: str = TwilioConfig.Debug):
        # logging
        self._logger = logger
        if not self._logger:
            self._logger = logging.getLogger(AppName+"."+__name__)
        self._httpLog = logging.getLogger(self._logger.name+".httpclient")
        self._httpLog.setLevel(20 if debug else 30)

        # client config
        # expects TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables
        self._client = TwilioClient(http_client=TwilioHttpClient(logger=self._httpLog))

        # to/from
        self.from_ = TwilioConfig.PhoneSource
        self.recipientList = TwilioConfig.Recipients

    # Get recipient list length
    @property
    def recipientListLength(self) -> int:
        return len(self.recipientList)

    # Default SMS sender
    # Arg: string message body.
    # Returns: Tuple[nothingSent: bool, List[sentStatus: Message]]. nothingSent is True if all messages failed to send, False if any message succeeded
    # Returns: list of (recipient, TwilioRestException.msg, TwilioRestException.status) for all exceptions occured. Empty list on complete success
    def send(self, body: str) -> Tuple[bool, List[Message]]:
        messages = []
        failedCount = 0
        nothingSent = False

        if not body:
            self._logger.error("Message body cannot be empty!")
            return TwilioSMSClient.ClientReturn(nothingSent=True,
                                                messages=messages)
        self._logger.info("Sending SMS with Twilio")

        # Send Loop
        for recipient in self.recipientList:
            try:
                # test for valid recipient
                Message.model_validate({"recipient": recipient})

                # send message
                msg = self._client.messages.create(from_=self.from_,
                                                   to=recipient,
                                                   body=body)
                """
                sid - unique twilio message id
                status - status of message (queued, sending, sent, failed, delivered, undelivered, receiving, received)
                error_code - Error code if message status is failed or undeliverd, otherwise None
                error_message - Description of error_code, None if no error
                """
                messages.append(Message(messageId=msg.sid,
                                        recipient=recipient,
                                        status=msg.status,
                                        errorCode=msg.error_code,
                                        errorMessage=msg.error_message))

                if msg.status == "canceled" or msg.status == "failed":
                    self._logger.warning("Created message {msg.sid} to {recipient}, but with status = {msg.status}")
                else:
                    self._logger.info(f"Successfully created message {msg.sid} to {recipient}. Status = {msg.status}")

            except TwilioRestException as e:
                self._logger.error(f"\"{e.msg}\" Status = {e.status}")
                messages.append(Message(recipient=recipient,
                                        status="failed",
                                        errorCode=e.status,
                                        errorMessage=e.msg))
                failedCount += 1

            except ValidationError as e:
                self._logger.error(f"Unable to validate Message: {e}")
                failedCount += 1

            except Exception as e:
                self._logger.error(f"Unexpected error when sending message to {recipient}: {e}")
                failedCount += 1

        if not failedCount:
            self._logger.info("All SMS sent successfully.")
        else:
            self._logger.warning(f"Failed to send {failedCount} message(s).")

        if failedCount >= self.recipientListLength:
            self._logger.warning("Unable to send anything with Twilio. Likely throttled, no valid recipients, or invalid from number.")
            nothingSent = True

        return TwilioSMSClient.ClientReturn(nothingSent=nothingSent,
                                            messages=messages)


if __name__ == "__main__":
    # testing - assumes good config from settings.TwilioConfig
    TestClient = TwilioSMSClient(debug=True)
    recipients = TestClient.recipientList.copy()
    source = TestClient.from_

    assert TestClient.recipientListLength == len(recipients)

    # messages sent successfully
    returnVal = TestClient.send("Testing...")
    assert not returnVal.nothingSent

    # None message body not sent successfully
    returnVal = TestClient.send(None)
    assert returnVal.nothingSent

    # one message failed to send, rest sent successfully
    TestClient.recipientList.append("+1aaabbbcccc")
    returnVal = TestClient.send("Testing...")
    TestClient.recipientList.pop()
    assert not returnVal.nothingSent
    assert returnVal.messages[-1].recipient == "+1aaabbbcccc"  # message should be added to end of list

    # one message failed to send (because of Validation error), rest sent successfully
    TestClient.recipientList.append("aaa")
    returnVal = TestClient.send("Testing...")
    TestClient.recipientList.pop()
    assert not returnVal.nothingSent
    assert returnVal.messages[-1].recipient != "aaa"  # message should not be added due to ValidationError

    # invalid from address; all messages failed to send
    TestClient.from_ = "+1aaabbbcccc"
    returnVal = TestClient.send("Testing...")
    TestClient.from_ = source
    assert returnVal.nothingSent
