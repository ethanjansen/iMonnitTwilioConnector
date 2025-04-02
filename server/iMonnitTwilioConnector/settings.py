# settings.py
# By: Ethan Jansen
# OS Environment Variable Settings

from flask.logging import default_handler
import logging
from os import environ, urandom
import sys


# Logging Config
appLog = logging.getLogger(__package__)
default_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(name)s: %(message)s"))
appLog.addHandler(default_handler)
appLog.setLevel(logging.INFO)
SettingsLog = logging.getLogger(__name__)


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
    ServerSecret = environ.get("IMONNIT_TWILIO_CONNECTOR_SECRET", urandom(24))


class TwilioConfig:
    # Required Settings
    try:
        # AccoundSID = # accessed directly
        # AuthToken = # accessed directly
        PhoneSource = environ["TWILIO_PHONE_SRC"]
    except Exception as e:
        errorHandler(e)

    # Optional Settings
    Recipients = list(filter(None, environ.get("TWILIO_PHONE_RCPTS", "").split(",")))
    Debug = "TWILIO_DEBUG" in environ  # INFO if set, WARN if unset


class DbConfig:
    # Required Settings
    Host = "imonnitTwilioConnector-db"

    try:
        User = environ["MARIADB_USER"]
        Password = environ["MARIADB_PASSWORD"]
        Database = environ["MARIADB_DATABASE"]
    except Exception as e:
        errorHandler(e)

    # Optional Settings
    Port = environ.get("MYSQL_TCP_PORT", 3306)
