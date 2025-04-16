# iMonnitTwilioConnector
## A Python server to host an iMonnit rule webhook, sending notifications via Twilio. Also logs events and sent messages to internal database.
### By: Ethan Jansen

## Setup:
 - Sign up for Twilio and go to the [Console](https://www.twilio.com/console) to get account_sid. [Create an API key](https://console.twilio.com/us1/account/keys-credentials/api-keys) and save the key sid and secret. Also purchase a Twilio phone number for phone_src.
    - Messages created with app will already specify status callback url if enabled. No need to specify in Twilio console.
    - Twilio status callback configuration expects https, so only use with proxy such as nginx.
 - Start and initialize external MariaDB database (with docker)
 - Set environment variables following [settings.py](iMonnitTwilioConnector/settings.py)
 - Build wheel with `python -m build --wheel` (pip depends: `build`). Install with `pip install dist/imonnittwilioconnector-1.0.4-py3-none-any.whl`. Optionally install `waitress`: `pip install waitress`; and run with production server: `waitress-server --call iMonnitTwilioConnector:create_app`.
 - Log in to [iMonnit](https://www.imonnit.com/API/) and create a rule webhook. Specify server and configure basic authentication. Finally, add rules to rule webhook.
 
## Usage:
 - iMonnit webhook listens to `http://<domain>:<port>/webhook/imonnit`
 - Twilio status callback webhook listens to `http://<domain>:<port>/webhook/twilio`
    - Note: Twilio callbacks will initially fail Basic Authorization, but will retry successfully.
 - Requires HTTP Basic Auth

## Environment Variable Configuration:
 - `IMONNIT_TWILIO_CONNECTOR_WH_USER`: webhook HTTP basic authentication username for iMonnit and Twilio.
 - `IMONNIT_TWILIO_CONNECTOR_WH_PASS`: webhook HTTP basic authentication password for iMonnit and Twilio.
 - `IMONNIT_TWILIO_CONNECTOR_HOSTNAME`: public-facing server domain name. Used for send Twilio status callback url info.
 - `IMONNIT_TWILIO_CONNECTOR_SECRET`: (optional) Flask secret key used to protect user session data. Mostly unused. Set automatically if not set.
 - `TWILIO_ACCOUNT_SID`: Twilio account_sid to use for sending SMS messages.
 - `TWILIO_API_SID`: Twilio API key sid. Used for Twilio authentication.
 - `TWILIO_API_SECRET`: Twilio API key secret. Used for Twilio authentication.
 - `TWILIO_PHONE_SRC`: Twilio phone number used to send SMS messages from. Requires A2P 10DLC registration in USA. Needs to be in E.164 format.
 - `TWILIO_PHONE_RCPTS`: (optional) comma-separated list of phone numbers to send SMS notification messages to. Need to be in E.164 format.
 - `TWILIO_CALLBACK`: (optional, defaults to "false") "true" or "false" boolean to enable Twilio status callbacks.
 - `TWILIO_ERROR_DICTIONARY_FILE`: (optional, defaults for docker configuration) path to json file of twilio error codes for error messages look up. If path is invalid, error messages from twilio status callback will be empty.
 - `TWILIO_DEBUG`: (optional, defaults to "false") "true" or "false" boolean to increase Twilio client logging verbosity.
 - `MARIADB_USER`: MariaDB username for database connection.
 - `MARIADB_PASSWORD`: MariaDB password for database connection.
 - `MARAIDB_DATABASE`: MariaDB database name for database connection.
 - `MYSQL_HOSTNAME`: (optional, defaults to 3306) MariaDB database connection hostname/address.
 - `MYSQL_TCP_PORT`: (optional, defaults for docker configuration) MariaDB database connection port.
