#!/bin/bash

# edits configs in /etc/nginx/user_conf.d/model by replacing following environment variables and copies to /etc/nginx/user_conf.d/
# environment variables: ${IMONNIT_TWILIO_CONNECTOR_HOSTNAME}, ${IMONNIT_TWILIO_CONNECTOR_PORT}

if [ -z "$IMONNIT_TWILIO_CONNECTOR_HOSTNAME" ] || [ -z "$IMONNIT_TWILIO_CONNECTOR_PORT" ]; then
  echo "hostname and port environment variables are not set! Exiting..."
  exit 1
fi

while IFS= read -r -d $'\0' model; do
  echo "Reading model: ${model}"

  sed -e "s/\${IMONNIT_TWILIO_CONNECTOR_HOSTNAME}/${IMONNIT_TWILIO_CONNECTOR_HOSTNAME}/g" \
      -e "s/\${IMONNIT_TWILIO_CONNECTOR_PORT}/${IMONNIT_TWILIO_CONNECTOR_PORT}/g" \
      "$model" > "/etc/nginx/user_conf.d/$(basename -- "$model")"
done < <(find /etc/nginx/user_conf.d/model/ -maxdepth 1 -type f -print0)

# call original CMD 
/scripts/start_nginx_certbot.sh
