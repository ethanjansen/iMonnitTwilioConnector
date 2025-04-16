# iMonnitTwilioConnector
## A Python server to host an iMonnit rule webhook, sending notifications via Twilio. Also logs events and sent messages to internal database.
### By: Ethan Jansen

## Setup:
 - Sign up for Twilio and go to the [Console](https://www.twilio.com/console) to get account_sid. [Create an API key](https://console.twilio.com/us1/account/keys-credentials/api-keys) and save the key sid and secret. Also purchase a Twilio phone number for phone_src.
    - Messages created with app will already specify status callback url if enabled. No need to specify in Twilio console.
        - To enable ensure `TWILIO_CALLBACK="true"`.
 - Set environment variables and exposed ports in [compose.yml](compose.yml). See python server [README](./server/README.md) for environment variable reference.
 - Start docker swarm with `sudo docker compose --profile with_local_proxy up -d` from the project folder.
    - Ensure that `IMONNIT_TWILOI_CONNECTOR_PORT`, `IMONNIT_TWILIO_CONNECTOR_HOSTNAME` are specified or else nginx will not run. Also ensure `IMONNIT_TWILIO_CONNECTOR_USE_HTTPS="true"`.
    - To start without included Nginx reverse proxy run with: `sudo docker compose up -d`
 - Log in to [iMonnit](https://www.imonnit.com/API/) and create a rule webhook. Specify server and configure basic authentication. Finally, add rules to rule webhook via "server action".
 
## Usage:
 - iMonnit webhook listens to `https://<domain>/webhook/imonnit`
    - Also listens locally behind Nginx at `http://<host>:$IMONNIT_TWILIO_CONNECTOR_PORT/webhook/imonnit`
 - Twilio status callback webhook listens to `https://<domain>/webhook/twilio`
    - Also listens locally behind Nginx at `http://<host>:$IMONNIT_TWILIO_CONNECTOR_PORT/webhook/twilio`
    - Note: Twilio callbacks will initially fail Basic Authorization, but will retry successfully.
 - Requires HTTP Basic Auth

## Testing:
 - Start a separate docker container (different ports) and run [tests/external/test.sh](server/tests/external/test.sh) to test full stack: `sudo docker run --network imonnittwilioconnector_default -v /<project root>/server/tests:/server/tests --rm imonnittwilioconnector-server:latest /server/tests/external/test.sh`
    - Make sure to rename and set [test environment variables](server/tests/external/defaultTesting.env-example) accordingly.
    - Also ensure database is running (done easily by running entire swarm before testing, proxy optional).
 - Individual unit tests can be run by executing python files such as: [dataTypes](server/iMonnitTwilioConnector/dataTypes.py), [db.py](server/iMonnitTwilioConnector/db.py), and [twilioClient.py](server/iMonnitTwilioConnector/twilioClient.py).
    - This is done, easily, with the following docker commands (ensure database is running for `db.py` testing). This is best done with the docker swarm already running. Also ensure the [test environment variables](server/tests/external/defaultTesting.env-example) are set accordingly.
        - dataTypes: `sudo docker run --network imonnittwilioconnector_default -v /<project root>/tests:/server/tests --rm imonnittwilioconnector-server ". /server/tests/external/defaultTesting.env; python -m iMonnitTwiloiConnector.dataTypes`
        - db: `sudo docker run --network imonnittwilioconnector_default -v /<project root>/tests:/server/tests --rm imonnittwilioconnector-server ". /server/tests/external/defaultTesting.env; python -m iMonnitTwiloiConnector.db`
        - twilioClient: `sudo docker run --network imonnittwilioconnector_default -v /<project root>/tests:/server/tests --rm imonnittwilioconnector-server ". /server/tests/external/defaultTesting.env; python -m iMonnitTwiloiConnector.twilioClient`

## Access internal database:
 - A separate mariadb docker container can be run to access the database: `sudo docker run -it --network imonnittwilioconnector_default --rm mariadb:11.4.5-noble mariadb -P3306 -himonnitTwilioConnector-db -uuserWhatever -puserWhateverPass dbTest`
    - Make sure to set credentials, database name, and port correctly.
