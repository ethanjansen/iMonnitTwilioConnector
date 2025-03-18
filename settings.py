# settings.py
# By: Ethan Jansen
# OS Environment Variable Settings

from flask.logging import default_handler
import logging
from os import environ
import sys

# Used for flask app name & logger
AppName = "iMonnitTwilioConnector"

# Logging Config
appLog = logging.getLogger(AppName)
default_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(name)s: %(message)s"))
appLog.addHandler(default_handler)
appLog.setLevel(logging.INFO)
SettingsLog = logging.getLogger(AppName+"."+__name__)


# Settings exception handler
def errorHandler(e):
    SettingsLog.fatal(f"Missing environment variable: {e}")
    sys.exit(1)


# Settings:


class ImonnitTwilioConnectorConfig:
    # Required Settings
    try:
        WebhookUser = environ["IMONNIT_TWILIO_CONNECTOR_WH_USER"]
        WebhookPassword = environ["IMONNIT_TWILIO_CONNECTOR_WH_PASS"]
    except KeyError as e:
        errorHandler(e)

    # Optional Settings
    ServerPort = environ.get("IMONNIT_TWILIO_CONNECTOR_PORT", 5080)


class TwilioConfig:
    # Required Settings
    try:
        # AccoundSID = # accessed directly
        # AuthToken = # accessed directly
        PhoneSource = environ["TWILIO_PHONE_SRC"]
    except Exception as e:
        errorHandler(e)

    # Optional Settings
    Recipients = environ.get("TWILIO_PHONE_RCPTS", "").split(",")
