# dataTypes.py
# By: Ethan Jansen
# data class with pydantic validation for webhooks

from datetime import datetime
from pydantic import BaseModel, BeforeValidator, computed_field, Field, ValidationError
from typing import List, Tuple, TypeAlias
from typing_extensions import Annotated


def _emptyStrToNone(s: str | None) -> None:
    if s is None or (isinstance(s, str) and s.strip() == ""):
        return None
    raise ValueError("Value is not empty")


class _customDTValidator:
    def __init__(self, formatString: str):
        self.formatString = formatString

    def validate(self, dt: str | datetime) -> datetime:
        # validate after _emptyStrToNone. dt cannot be None or ""
        if isinstance(dt, datetime):
            return dt
        elif isinstance(dt, str):
            return datetime.strptime(dt, self.formatString).astimezone().replace(tzinfo=None)
        raise TypeError("dt is not string or datetime")


class _DTFactory:
    def __init__(self, dKey: str, tKey: str):
        self.dKey = dKey
        self.tKey = tKey

    def convert(self, data: dict[str, str]) -> str | None:
        d = data[self.dKey]
        t = data[self.tKey]

        if d and t:
            return f"{d} {t}"
        return None


EmptyStrToNone: TypeAlias = Annotated[None, BeforeValidator(_emptyStrToNone)]

OptionalStrInitVal = Annotated[str, Field(init_var=True, exclude=True)]
NullableStr = EmptyStrToNone | str
NullableInt = EmptyStrToNone | int
NullableUnsignedInt = EmptyStrToNone | Annotated[int, Field(gt=0)]
NullableDT = EmptyStrToNone | datetime
NullableFancyDTEvent = EmptyStrToNone | Annotated[datetime,
                                                  BeforeValidator(_customDTValidator("%Y-%m-%d %H:%M").validate)]
NullableFancyDTMessageSent = EmptyStrToNone | Annotated[datetime,
                                                        BeforeValidator(_customDTValidator("%a, %d %b %Y %H:%M:%S %z").validate)]
NullableFancyDTMessageDelivered = EmptyStrToNone | Annotated[datetime,
                                                             BeforeValidator(_customDTValidator("%y%m%d%H%M").validate)]


class Message(BaseModel):  # this may not match keys of callback
    id: NullableUnsignedInt = None
    eventId: NullableUnsignedInt = None
    messageId: EmptyStrToNone | Annotated[str, Field(min_length=34, max_length=34)] = None
    recipient: Annotated[str, Field(min_length=12, max_length=30)]
    status: NullableStr = None
    sentDT: NullableFancyDTMessageSent = None
    deliveredDT: NullableFancyDTMessageDelivered = None
    errorCode: NullableInt = None
    errorMessage: NullableStr = None

    created: NullableDT = None
    updated: NullableDT = None

    def toSqlImport(self) -> Tuple[int | None,
                                   str | None,
                                   str,
                                   str | None,
                                   datetime | None,
                                   datetime | None,
                                   int | None,
                                   str | None]:
        return (self.eventId,
                self.messageId,
                self.recipient,
                self.status,
                self.sentDT,
                self.deliveredDT,
                self.errorCode,
                self.errorMessage)

    def toSqlUpdate(self) -> Tuple[str | None,
                                   datetime | None,
                                   datetime | None,
                                   int | None,
                                   str | None,
                                   datetime | None,
                                   str | None]:
        if self.messageId is None:
            raise ValueError("Cannot update SQL Message with null messageID")

        return (self.status,
                self.sentDT,
                self.deliveredDT,
                self.errorCode,
                self.errorMessage,
                self.updated,
                self.messageId)


class Event(BaseModel):
    id: NullableUnsignedInt = None
    rule: Annotated[str, Field(min_length=1)]
    subject: NullableStr = None
    deviceID: NullableInt = None
    name: NullableStr = None  # device name
    reading: NullableStr = None
    # originalReading is ignored

    date: OptionalStrInitVal = ""  # triggered date
    time: OptionalStrInitVal = ""  # triggered time
    readingDate: OptionalStrInitVal = ""
    readingTime: OptionalStrInitVal = ""
    originalReadingDate: OptionalStrInitVal = ""
    originalReadingTime: OptionalStrInitVal = ""

    triggeredDT: NullableFancyDTEvent = Field(default_factory=_DTFactory("date", "time").convert,
                                              validate_default=True
                                              )
    readingDT: NullableFancyDTEvent = Field(default_factory=_DTFactory("readingDate", "readingTime").convert,
                                            validate_default=True
                                            )
    originalReadingDT: NullableFancyDTEvent = Field(default_factory=_DTFactory("originalReadingDate", "originalReadingTime").convert,
                                                    validate_default=True
                                                    )

    acknowledgeURL: NullableStr = None
    # no messageNumber (messageCount)
    parentAccount: NullableStr = None
    networkID: NullableInt = None
    network: NullableStr = None
    accountID: NullableInt = None
    accountNumber: NullableStr = None
    companyName: NullableStr = None

    messages: Annotated[List[Message], Field(exclude=True)] = []

    created: NullableDT = None

    @computed_field
    @property
    def messageBody(self) -> str:
        dtString = ""
        if self.triggeredDT:
            dtString = self.triggeredDT.strftime("%Y-%m-%d %H:%M")

        return f"""{self.rule} triggered by {self.name} ({self.deviceID})
Time: {dtString}
Reading: {self.reading}
Acknowledge: {self.acknowledgeURL}"""

    @computed_field
    @property
    def messageCount(self) -> int:
        return len(self.messages)

    def setAllEventId(self, id: int | str) -> None:
        """Updates Event.id and Message.eventId for all messages"""
        if isinstance(id, str):
            id = int(id)
        self.id = id
        for msg in self.messages:
            msg.eventId = id

    def toSqlImport(self) -> Tuple[str,
                                   str | None,
                                   int | None,
                                   str | None,
                                   str | None,
                                   datetime | None,
                                   datetime | None,
                                   datetime | None,
                                   str | None,
                                   int,
                                   str | None,
                                   int | None,
                                   str | None,
                                   int | None,
                                   str | None,
                                   str | None]:
        return (self.rule,
                self.subject,
                self.deviceID,
                self.name,
                self.reading,
                self.triggeredDT,
                self.readingDT,
                self.originalReadingDT,
                self.acknowledgeURL,
                self.messageCount,
                self.parentAccount,
                self.networkID,
                self.network,
                self.accountID,
                self.accountNumber,
                self.companyName)

    def toSqlImportMessages(self) -> List[Tuple[int | None,
                                                str | None,
                                                str,
                                                str | None,
                                                datetime | None,
                                                datetime | None,
                                                int | None,
                                                str | None]]:
        returnList = []
        for msg in self.messages:
            returnList.append(msg.toSqlImport())
        return returnList


if __name__ == '__main__':
    # testing - no unittest here

    # no rule in Event
    exceptionThrown = False
    try:
        Event()
    except ValidationError:
        exceptionThrown = True
    assert exceptionThrown

    # event with None rule
    exceptionThrown = False
    try:
        Event(rule=None)
    except ValidationError:
        exceptionThrown = True
    assert exceptionThrown

    # event with "" rule
    exceptionThrown = False
    try:
        Event(rule="")
    except ValidationError:
        exceptionThrown = True
    assert exceptionThrown

    # event: test "" to None conversion
    EmptyToNoneEvent = Event(rule="rule",
                             id="",
                             subject="",
                             created=" "
                             )
    assert EmptyToNoneEvent.rule == "rule"
    assert EmptyToNoneEvent.id is None
    assert EmptyToNoneEvent.subject is None
    assert EmptyToNoneEvent.created is None
    assert EmptyToNoneEvent.messageCount == 0
    assert EmptyToNoneEvent.deviceID is None

    # event: test type conversion
    TypeConversionEvent = Event(rule="rule",
                                id="123",
                                created="2025-03-28T14:25")
    assert TypeConversionEvent.id == 123
    assert TypeConversionEvent.created == datetime(2025, 3, 28, 14, 25)

    # event: negative id
    exceptionThrown = False
    try:
        Event(rule="rule", id=-1)
    except ValidationError:
        exceptionThrown = True
    assert exceptionThrown

    # event: invalid datetime format
    exceptionThrown = False
    try:
        Event(rule="rule", created="03/28/2025 at 14.25.00")
    except ValidationError:
        exceptionThrown = True
    assert exceptionThrown

    # event: test D and T to DT
    DTEvent = Event(rule="rule",
                    time="14:25",
                    date="2025-03-28",
                    readingTime="14:25",
                    originalReadingDate="2025-03-28")
    assert DTEvent.triggeredDT == datetime(2025, 3, 28, 14, 25)
    assert DTEvent.readingDT is None
    assert DTEvent.originalReadingDT is None

    # message: no recipient
    exceptionThrown = False
    try:
        Message()
    except ValidationError:
        exceptionThrown = True
    assert exceptionThrown

    # message: recipient does not match expected length
    exceptionThrown = False
    try:
        Message(recipient="1234567890")
    except ValidationError:
        exceptionThrown = True
    assert exceptionThrown

    exceptionThrown = False
    try:
        Message(recipient="whatsapp:+123456789012345678900")
    except ValidationError:
        exceptionThrown = True
    assert exceptionThrown

    # valid message
    SimpleMsg = Message(recipient="+11234567890")
    assert SimpleMsg.recipient == "+11234567890"
    assert SimpleMsg.messageId is None

    # message: empty messageId
    EmptyMessageIdMsg = Message(recipient="+11234567890",
                                messageId="")
    assert EmptyMessageIdMsg.recipient == "+11234567890"
    assert EmptyMessageIdMsg.messageId is None

    # message: invalid messageId length
    exceptionThrown = False
    try:
        BadMessageIdMsg = Message(recipient="+11234567890",
                                  messageId="sm1234567890")
    except ValidationError:
        exceptionThrown = True
    assert exceptionThrown

    # message: valid messageId
    GoodMessageIdMsg = Message(recipient="+11234567890",
                               messageId="sm0123456789abcdefghijklmnopqrstuv")
    assert GoodMessageIdMsg.messageId == "sm0123456789abcdefghijklmnopqrstuv"

    # message: nullable types
    NullableMsg = Message(recipient="+11234567890",
                          id="",
                          status="",
                          sentDT="",
                          deliveredDT="",
                          errorCode="",
                          created="")
    assert NullableMsg.id is None
    assert NullableMsg.status is None
    assert NullableMsg.sentDT is None
    assert NullableMsg.deliveredDT is None
    assert NullableMsg.errorCode is None
    assert NullableMsg.created is None

    # message: type conversion
    testDT = datetime(2025, 3, 28, 14, 25)
    TypeConversionMsg = Message(recipient="+11234567890",
                                id="123",
                                sentDT="Fri, 28 Mar 2025 06:25:00 -0800",
                                deliveredDT="2503281425",
                                errorCode="123",
                                created="2025-03-28T14:25")
    assert TypeConversionMsg.id == 123
    assert TypeConversionMsg.errorCode == 123
    assert TypeConversionMsg.sentDT == testDT
    assert TypeConversionMsg.deliveredDT == testDT
    assert TypeConversionMsg.created == testDT

    # message: native DT's
    NativeDTMsg = Message(recipient="+11234567890",
                          sentDT=testDT,
                          deliveredDT=testDT,
                          created=testDT)
    assert NativeDTMsg.sentDT == testDT
    assert NativeDTMsg.deliveredDT == testDT
    assert NativeDTMsg.created == testDT

    # test normal usage
    testEventDT = datetime(2022, 4, 28, 14, 21)
    testOutputEventMsgBody = """Battery below 50% triggered by IOT Gateway - 56789 (56789)
Time: 2022-04-28 14:21
Reading: Battery: 10%
Acknowledge: https://staging.imonnit.com/Ack/1234"""
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
        "originalReading": "blah"
        }

    testOutputEvent = {
        "id": 1,
        "rule": "Battery below 50%",
        "subject": "Battery below 50%!",
        "deviceID": 56789,
        "name": "IOT Gateway - 56789",
        "reading": "Battery: 10%",
        "triggeredDT": testEventDT,
        "readingDT": testEventDT,
        "originalReadingDT": None,
        "acknowledgeURL": "https://staging.imonnit.com/Ack/1234",
        "parentAccount": None,
        "networkID": 4567,
        "network": "Test Network",
        "accountID": 123456,
        "accountNumber": "Example-Company",
        "companyName": "Example Company",
        "created": None,
        "messageBody": testOutputEventMsgBody,
        "messageCount": 3
        }
    testOutputMsg1 = {
        "id": None,
        "eventId": 1,
        "messageId": "SM0123456789abcdefghijklmnopqrstuv",
        "recipient": "+11234567890",
        "status": "queued",
        "sentDT": None,
        "deliveredDT": None,
        "errorCode": None,
        "errorMessage": None,
        "created": None,
        "updated": None
        }
    testOutputMsg2 = {
        "id": None,
        "eventId": 1,
        "messageId": None,
        "recipient": "+11234567891",
        "status": "failed",
        "sentDT": None,
        "deliveredDT": None,
        "errorCode": 429,
        "errorMessage": "Error sending SMS...",
        "created": None,
        "updated": None
        }
    testOutputMsg3 = {
        "id": None,
        "eventId": 1,
        "messageId": "SM0123456789abcdefghijklmnopqrstuv",
        "recipient": "+11234567892",
        "status": "delivered",
        "sentDT": datetime(2025, 3, 28, 14, 25),
        "deliveredDT": datetime(2025, 3, 28, 14, 26),
        "errorCode": None,
        "errorMessage": None,
        "created": None,
        "updated": testEventDT
        }
    testOutputEventSql = ("Battery below 50%",
                          "Battery below 50%!",
                          56789,
                          "IOT Gateway - 56789",
                          "Battery: 10%",
                          testEventDT,
                          testEventDT,
                          None,
                          "https://staging.imonnit.com/Ack/1234",
                          3,
                          None,
                          4567,
                          "Test Network",
                          123456,
                          "Example-Company",
                          "Example Company")
    testOutputMsgsSql = [(1,
                          "SM0123456789abcdefghijklmnopqrstuv",
                          "+11234567890",
                          "queued",
                          None,
                          None,
                          None,
                          None),
                         (1,
                          None,
                          "+11234567891",
                          "failed",
                          None,
                          None,
                          429,
                          "Error sending SMS..."),
                         (1,
                          "SM0123456789abcdefghijklmnopqrstuv",
                          "+11234567892",
                          "delivered",
                          datetime(2025, 3, 28, 14, 25),
                          datetime(2025, 3, 28, 14, 26),
                          None,
                          None)]
    testOutputMsg3UpdateSql = ("delivered",
                               datetime(2025, 3, 28, 14, 25),
                               datetime(2025, 3, 28, 14, 26),
                               None,
                               None,
                               testEventDT,
                               "SM0123456789abcdefghijklmnopqrstuv")

    TestEvent = Event(**testInputEvent)
    # good send
    TestEvent.messages.append(Message(recipient="+11234567890",
                                      messageId="SM0123456789abcdefghijklmnopqrstuv",
                                      status="queued",
                                      errorCode=None,
                                      errorMessage=None))

    # bad send
    TestEvent.messages.append(Message(recipient="+11234567891",
                                      messageId=None,
                                      status="failed",
                                      errorCode=429,
                                      errorMessage="Error sending SMS..."))
    # callback
    TestEvent.messages.append(Message(recipient="+11234567892",
                                      sentDT="Fri, 28 Mar 2025 06:25:00 -0800",
                                      deliveredDT="2503281426",
                                      messageId="SM0123456789abcdefghijklmnopqrstuv",
                                      status="delivered",
                                      errorCode=None,
                                      errorMessage=None,
                                      updated=testEventDT))

    TestEvent.setAllEventId(1)

    assert TestEvent.messageBody == testOutputEventMsgBody
    assert TestEvent.messageCount == 3

    assert TestEvent.model_dump() == testOutputEvent
    assert TestEvent.messages[0].model_dump() == testOutputMsg1
    assert TestEvent.messages[1].model_dump() == testOutputMsg2
    assert TestEvent.messages[2].model_dump() == testOutputMsg3

    assert TestEvent.toSqlImport() == testOutputEventSql
    assert TestEvent.toSqlImportMessages() == testOutputMsgsSql
    assert TestEvent.messages[2].toSqlUpdate() == testOutputMsg3UpdateSql

    # message: test invalid sql update
    exceptionThrown = False
    try:
        TestEvent.messages[1].toSqlUpdate()
    except ValueError:
        exceptionThrown = True
    assert exceptionThrown
