# __init__.py
# By: Ethan Jansen
# App factory and entrypoint

from flask import Flask
from time import sleep
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

    # test database connection -- allow delayed start
    dbFailedCount = 0
    while not dbConn.testConnection():
        if dbFailedCount > 5:
            app.logger.critical("Unable to connect to database! Exiting...")
            sys.exit(2)
        dbFailedCount += 1
        app.logger.warning("Database not ready! Waiting...")
        sleep(3)

    app.logger.info("Starting server.")

    # register blueprints
    from .webhook import webhookBp
    app.register_blueprint(webhookBp)

    return app
