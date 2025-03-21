FROM python:3.11.11-alpine3.21

# Create directory structure
RUN mkdir -p /app/src \
  && mkdir -p /app/build

# Install dependencies
COPY ./requirements.txt /app/build/
RUN apk add --no-cache --virtual .build-deps gcc musl-dev mariadb-connector-c-dev \
  && pip install --no-cache-dir -r /app/build/requirements.txt \
  && apk add --no-cache --virtual .runtime-deps mariadb-connector-c

# Setup app - use docker-compose to mount app src volume, set environment variables, and expose desired port
VOLUME /app/src
WORKDIR /app/src
ENTRYPOINT ["/usr/local/bin/python"]
CMD ["server.py"]
