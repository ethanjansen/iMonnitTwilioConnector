# iMonnitTwilioConnector
## A Python server to host an iMonnit rule webhook, sending notifications via Twilio. Also logs events and sent messages to interal database.
### By: Ethan Jansen

## Setup:
 - Sign up for Twilio and go to the [Console](https://www.twilio.com/console) to get auth_token and account_sid. Also purchase a Twilio phone number for phone_src.
 - Set environment variables and exposed ports in [compose.yml](compose.yml)
 - Start docker swarm with `docker compose up -d` from the project folder
 - Log in to [iMonnit](https://www.imonnit.com/API/) and create a rule webhook. Specify server and configure basic authentication. Finally, add rules to rule webhook.
 
## Usage:
 - iMonnit webhook listens to `https://<domain>/webhook/imonnit`
    - Also listens locally behind Nginx at `http://<host>:$IMONNIT_TWILIO_CONNECTOR_PORT/webhook/imonnit`
 - Requires HTTP Basic Auth

## Testing:
 - Start a separate docker container (different ports) and run [tests/external/test.sh](server/tests/external/test.sh) to test full stack. Make sure to rename and set [test environment variables](server/tests/external/defaultTesting.env-example) accordingly.
 - Individual unit tests can be run by executing python files such as: [dataTypes](server/iMonnitTwilioConnector/dataTypes.py), [db.py](server/iMonnitTwilioConnector/db.py), and [twilioClient.py](server/iMonnitTwilioConnector/twilioClient.py).

## Access internal database:
 - A separate mariadb docker container can be run to access the database: `sudo docker run -it --network imonnittwilioconnector_default --rm mariadb:11.4.5-noble mariadb -P3306 -himonnitTwilioConnector-db -uuserWhatever -puserWhateverPass dbTest`
    - Make sure to set credentials, database name, and port correctly.
