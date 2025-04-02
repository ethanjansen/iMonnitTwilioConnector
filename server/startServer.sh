#!/bin/sh

waitress-serve --listen 0.0.0.0:"$IMONNIT_TWILIO_CONNECTOR_PORT" --no-ipv6 --call iMonnitTwilioConnector:create_app 
