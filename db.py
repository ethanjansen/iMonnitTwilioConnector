# db.py
# By: Ethan Jansen
# MariaDB Connector

import logging
import mariadb
from settings import AppName, DbConfig
from dataTypes import Event, Message
# testing
from datetime import datetime
import sys


class DbConnector:
    _insertEventSQL = "INSERT INTO Event (Rule, Subject, DeviceId, Device, Reading, TriggeredDT, ReadingDT, " \
                    "OriginalReadingDT, AcknowledgeUrl, MessageNumber, ParentAccount, NetworkId, Network, AccountId, " \
                    "AccountNumber, CompanyName) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"

    _insertMessageSQL = "INSERT INTO Message (EventId, MessageId, Recipient, Status, SentDT, DeliveredDT, " \
                        "ErrorCode, ErrorMessage) VALUES (?,?,?,?,?,?,?,?)"

    _updateMessageSQL = "UPDATE Message SET Status=?, SentDT=?, DeliveredDT=?, ErrorCode=?, ErrorMessage=?, " \
                        "Updated=? WHERE MessageId=? LIMIT 1"

    _getMessageSQL = "SELECT Id FROM Message WHERE MessageId=? LIMIT 1"

    def __init__(self):
        self.isConnected = False
        self.hasCursor = False

        self._connection = None
        self._cursor = None

        self._logger = logging.getLogger(AppName+"."+__name__)

    def __del__(self):
        self._disconnect()

    def _connect(self):
        """Wrapper for mariadb.connect().cursor(). Handles config from settings.DbConfig. Returns cursor."""
        self._connection = mariadb.connect(
                host=DbConfig.Host,
                port=DbConfig.Port,
                user=DbConfig.User,
                password=DbConfig.Password,
                database=DbConfig.Database
                )
        self.isConnected = True

        self._cursor = self._connection.cursor()
        self.hasCursor = True

        return self._cursor

    def _disconnect(self):
        if self.hasCursor and self._cursor:
            self._cursor.close()
        if self.isConnected and self._connection:
            self._connection.close()

        self.hasCursor = False
        self.isConnected = False

    def testConnection(self):
        """Test ability to connect/disconnect from database."""
        """"Returns True on success, False otherwise."""
        try:
            self._connect()
            self._disconnect()
            self._logger.info("Successfully connected to database")
            return True
        except Exception as e:
            self._logger.fatal(f"Test connection: Unable to connect to db: {e}")
            return False

    def addEventWithMessages(self, event):
        """Connects to DB, inserts event with messages, then disconnects from DB."""
        """Takes dataTypes.Event instance (which may hold a list of dataTypes.Message instances)."""
        """"Returns True on success, False otherwise."""
        try:
            if not self.isConnected:
                self._connect()

            self._connection.begin()

            # Add Event
            self._cursor.execute(DbConnector._insertEventSQL, event.toSqlImport())
            id = self._cursor.lastrowid

            if id is None:
                raise ValueError("id is None after inserting Event into db")

            event.setAllEventId(id)

            # Add Messages
            messageIds = []
            for messageImport in event.toSqlImportMessages():
                self._cursor.execute(DbConnector._insertMessageSQL, messageImport)
                messageIds.append(self._cursor.lastrowid)

            self._connection.commit()

            self._logger.info(f"Added Event to db with id {id}")
            for messageId in messageIds:
                self._logger.info(f"Added Message to db with id {messageId}")

        except Exception as e:
            self._connection.rollback()
            self._logger.error(f"Error adding Event with Messages to db: {e}")
            return False

        self._disconnect()
        return True

    def updateMessage(self, message):
        """Connects to DB, updates one message matching message.messageId, then disconnects from DB."""
        """Takes dataTypes.Message instance. Returns True on success, False otherwise."""
        try:
            if not self.isConnected:
                self._connect()

            self._connection.begin()

            # get id for logging and test for errors
            self._cursor.execute(DbConnector._getMessageSQL, (message.messageId,))
            id = self._cursor.fetchone()
            if id is None:
                raise ValueError("No Message matches MessageId in db for update")
            id = id[0]

            # Update message
            # message.messageId is valid or the following will raise ValueError
            self._cursor.execute(DbConnector._updateMessageSQL, message.toSqlUpdate())

            self._connection.commit()

            self._logger.info(f"Updated Message in db with id {id}")

        except Exception as e:
            self._connection.rollback()
            self._logger.error(f"Error updating message: {e}")
            return False

        self._disconnect()
        return True


if __name__ == "__main__":
    connector = DbConnector()
    if not connector.testConnection():
        sys.exit(2)

    # test data
    testEventDT = datetime(2022, 4, 28, 14, 21)
    testInputEvent = {
        "subject": "Battery below 50%!",
        "reading": "Battery: 10%",
        "rule": "Battery below 50%",
        "date": "2022-4-28",
        "time": "14:21",
        "readingDate": "2022-4-28",
        "readingTime": "14:21",
        "acknowledgeURL": "https://staging.imonnit.com/Ack/1234",
        "parentAccount": "",
        "deviceID": "56789",
        "name": "IOT Gateway - 56789",
        "networkID": "4567",
        "network": "Test Network",
        "accountID": "123456",
        "accountNumber": "Example-Company",
        "companyName": "Example Company",
        }
    TestEvent = Event(**testInputEvent)

    # event with no messages
    assert connector.addEventWithMessages(TestEvent)

    TestEvent.messages.append(Message(recipient="+11234567890",
                                      messageId="SM0123456789abcdefghijklmnopqrstuv",
                                      status="queued",
                                      errorCode=None,
                                      errorMessage=None))
    TestEvent.messages.append(Message(recipient="+11234567891",
                                      messageId=None,
                                      status="failed",
                                      errorCode=429,
                                      errorMessage="Error sending SMS..."))
    TestEvent.messages.append(Message(recipient="+11234567892",
                                      sentDT="Fri, 28 Mar 2025 06:25:00 -0800",
                                      deliveredDT="2503281426",
                                      messageId="SM0123456789abcdefghijklmnopqrstuv",
                                      status="delivered",
                                      errorCode=None,
                                      errorMessage=None,
                                      updated=testEventDT))

    # event with messages
    assert connector.addEventWithMessages(TestEvent)

    # update message that doesn't exist
    failedReturn = connector.updateMessage(Message(recipient="+11234567890",
                                                   messageId="SM0123456789abcdefghijklm-nonexist",
                                                   sentDT=testEventDT,
                                                   updated=testEventDT,
                                                   status="sent"))
    assert not failedReturn

    # update message -- unique messageId (real world)
    TestMessage = Message(recipient="+11234567890",
                          messageId="SM0123456789abcdefghijklmno-unique",
                          status="queued",
                          errorCode=None,
                          errorMessage=None)
    TestEvent2 = Event(**testInputEvent)
    TestEvent2.subject = "update message unique tests"
    TestEvent2.messages.append(TestMessage)
    assert connector.addEventWithMessages(TestEvent2)

    TestMessage.status = "failed"
    TestMessage.errorCode = 400
    TestMessage.errorMessage = "test update..."
    TestMessage.updated = testEventDT
    assert connector.updateMessage(TestMessage)

    # update message -- non-unique messageId
    TestMessage.messageId = "SM0123456789abcdefghijklmnopqrstuv"
    TestMessage.errorMessage = "test update multiple..."
    assert connector.updateMessage(TestMessage)
