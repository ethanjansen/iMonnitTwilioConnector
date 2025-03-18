# server.py
# By: Ethan Jansen
# Websocket server for iMonnit--sends text with Twilio. Requires Basic Authorization.

from flask import Flask, request
from werkzeug.exceptions import ServiceUnavailable, InternalServerError
import logging
from functools import wraps
from os import environ
from time import sleep  # testing

# Register app
app = Flask(__name__)


# Helper functions
# Authentication check
def checkAuth(username, password):
    userCheck = username == environ.get("IMONNIT_TWILIO_CONNECTOR_WH_USER", "Hello")
    passCheck = password == environ.get("IMONNIT_TWILIO_CONNECTOR_WH_PASS", "World")

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
    # Log
    app.logger.info(f"Data received: {request.json}")

    # Do Stuff - Example
    data = request.json

    if data["key1"] == "good":
        pass
    elif data["key1"] == "delayed":
        sleep(30)
    else:
        raise ServiceUnavailable(description="Twilio Throttling Error")

    # Return success
    return ("Success", 200)


# Run
if __name__ == "__main__":
    app.logger.setLevel(logging.INFO)
    app.run(host="0.0.0.0", port=environ.get("IMONNIT_TWILIO_CONNECTOR_PORT", 5080))
