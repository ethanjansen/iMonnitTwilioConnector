# auth.py
# By: Ethan Jansen
# Basic HTTP Authentication wrapper for flask.
# Password are not currently hashed (their from env vars anyway)

from flask import request
from functools import wraps
import logging
from .settings import ImonnitTwilioConnectorConfig


logger = logging.getLogger(__name__)


# Authentication check
def checkAuth(username, password):
    userCheck = username == ImonnitTwilioConnectorConfig.WebhookUser
    passCheck = password == ImonnitTwilioConnectorConfig.WebhookPassword

    return userCheck and passCheck


# Authentication wrapper
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not (auth and checkAuth(auth.username, auth.password)):
            logger.warning("Unauthorized Basic Auth")
            return ("Unauthorized", 401, {"WWW-Authenticate": 'Basic realm="Login Required"'})

        return f(*args, **kwargs)
    return decorated_function
