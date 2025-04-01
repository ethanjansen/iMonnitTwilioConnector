# Full Stack Test
#### Note: this currently does not verify db data and twilio sms data

## Usage:

 - Move `defaultTesting.env-example` to `defaultTesting.env` and add Twilio secrets. Change port and database credentials as necessary.
 - Start a separate docker container from the app image but change the entrypoint to `tests/external/test.sh`.
 - Monitor docker log, test database, and Twilio virtual phone.
