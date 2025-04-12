# iMonnitTwilioConnector
## A Python server to host an iMonnit rule webhook, sending notifications via Twilio. Also logs events and sent messages to internal database.
### By: Ethan Jansen

## Setup:
 - Sign up for Twilio and go to the [Console](https://www.twilio.com/console) to get account_sid. [Create an API key](https://console.twilio.com/us1/account/keys-credentials/api-keys) and save the key sid and secret. Also purchase a Twilio phone number for phone_src.
 - Start and initialize external MariaDB database (with docker)
 - Set environment variables following [settings.py](iMonnitTwilioConnector/settings.py)
 - Build wheel with `python -m build --wheel` (pip depends: `build`). Install with `pip install dist/imonnittwilioconnector-1.0.0-py3-none-any.whl`. Optionally install `waitress`: `pip install waitress`; and run with production server: `waitress-server --call iMonnitTwilioConnector:create_app`.
 - Log in to [iMonnit](https://www.imonnit.com/API/) and create a rule webhook. Specify server and configure basic authentication. Finally, add rules to rule webhook.
 
## Usage:
 - iMonnit webhook listens to `https://<domain>/webhook/imonnit`
    - Also listens locally behind Nginx at `http://<host>:$IMONNIT_TWILIO_CONNECTOR_PORT/webhook/imonnit`
 - Requires HTTP Basic Auth
