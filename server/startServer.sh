#!/bin/sh

if [ "$IMONNIT_TWILIO_CONNECTOR_USE_HTTPS" = "true" ]; then
  echo "Using HTTPS"
  waitress-serve --listen 0.0.0.0:"$IMONNIT_TWILIO_CONNECTOR_PORT" --no-ipv6 --url-scheme=https --call iMonnitTwilioConnector:create_app 
else
  waitress-serve --listen 0.0.0.0:"$IMONNIT_TWILIO_CONNECTOR_PORT" --no-ipv6 --call iMonnitTwilioConnector:create_app 
fi
