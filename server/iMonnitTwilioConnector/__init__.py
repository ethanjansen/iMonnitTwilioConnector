# __init__.py
# By: Ethan Jansen
# App factory and entrypoint

from flask import Flask
import sys
from . import settings  # this also tests all environment variables and configures logging
from .db import DbConnector
from .twilioClient import TwilioSMSClient


# instantiate twilio client and db connector
smsClient = TwilioSMSClient()
dbConn = DbConnector()


def create_app():
    # Configure app
    app = Flask(__package__, instance_relative_config=True, static_folder=None)
    app.config.from_mapping(SECRET_KEY=settings.ImonnitTwilioConnectorConfig.ServerSecret)

    # test database connection
    if not dbConn.testConnection():
        app.logger.critical("Unable to connect to database! Exiting...")
        sys.exit(2)

    app.logger.info("Starting server.")

    # register blueprints
    from .webhook import webhookBp
    app.register_blueprint(webhookBp)

    return app
