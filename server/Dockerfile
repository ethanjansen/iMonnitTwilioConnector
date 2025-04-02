FROM python:3.11.11-alpine3.21

# Create directory structure
RUN mkdir /server

# Install dependencies
COPY . /server
RUN apk add --no-cache --virtual .build-deps gcc musl-dev mariadb-connector-c-dev \
  && pip install --no-cache-dir build waitress \
  && python -m build --wheel /server \
  && pip install --no-cache-dir /server/dist/imonnittwilioconnector-1.0.0-py3-none-any.whl \
  && apk add --no-cache --virtual .runtime-deps mariadb-connector-c curl \
  && apk del .build-deps \
  && rm -rf /server/iMonnitTwilioConnector /server/LICENSE /server/pyproject.toml /server/README.md \
  && mkdir /server/tests

# Setup server - use docker-compose to mount server tests volume, set environment variables, and expose desired port
VOLUME /server/tests
WORKDIR /server
ENTRYPOINT ["/bin/sh", "-c"]
CMD ["startServer.sh"]
