#!/bin/sh

# External test script
# Tests most of full stack with curl
# Sets env variables and POSTS different data and compares against expected return data and code
# Run from container app container
#
# Does Not:
#   - confirm data in db (yet)
#   - confirm Twilio SMS contents
#   - confirm proper server logging


# Global vars:
serverPath="/app/iMonnitTwilioConnector"
testScriptPath="/app/tests/external"
route="http://localhost:${IMONNIT_TWILIO_CONNECTOR_PORT}/webhook/imonnit"

serverPID=


# Sets up default env variables. Saves existing to restore later to saved.env
setupEnv(){
  if [ ! -f "${testScriptPath}/defaultTesting.env" ]; then
    echo "[TEST] defaultTesting.env does not exist! Exiting..."
    exit 2
  fi

  export -p > "$testScriptPath/saved.env"
  . "${testScriptPath}/defaultTesting.env"
}


# Restores env variables.
# Thanks: https://unix.stackexchange.com/questions/308421/how-to-store-load-exported-environment-variables-to-from-a-file
restoreEnv(){
  blacklisted(){
    case $1 in
      PWD|OLDPWD|SHELL|STORAGE|-*) return 0 ;;
      *) return 1 ;;
    esac
  }

  eval '
    export(){
      blacklisted "${1%%=*}" || unset -v "${1%%=*}"
    }
  '"$(export -p)"
  export(){
    blacklisted "${1%%=*}" || command export "$@"
  }

  . "${testScriptPath}/saved.env"
  unset -f export blacklisted
  rm "${testScriptPath}/saved.env"
}


# Parses curl reponse $1, and checks return data $2 and return code $3 
# Expects curl param '-w "\n%{response_code}"'
curlPost_helper(){
  status=$(echo "$1" | tail -n 1)
  body=$(echo "$1" | head -n -1)
  
  fails=1
  
  if [ "$status" != "$3" ]; then
    printf "[TEST] Status does not match:\n  Expected: %s\n  Got: %s\n" "$3" "$status"
    fails=0
  fi
  if [ "$body" != "$2" ]; then
    printf "[TEST] Body does not match:\n  Expected: %s\n  Got: %s\n" "$2" "$body"
    fails=0
  fi

  if [ "$fails" = 0 ]; then
    killApp
    restoreEnv
    exit 1
  else
    echo "[TEST] Passed!"
  fi
}


# Posts data $1 to localhost:$IMONNIT_TWILIO_CONNECTOR_PORT and checks return data $2 and return code $3
curlPost(){
  curlPost_helper "$(curl -s \
                     -w "\n%{response_code}" \
                     -X POST \
                     -H "Content-Type: application/json" \
                     -d "$1" \
                     "$route"
                    )" "$2" "$3"
}


# same as curlPost(), but with basic auth using $IMONNIT_TWILIO_CONNECTOR_WH_USER:$IMONNIT_TWILIO_CONNECTOR_WH_PASS
curlPostWithAuth(){
  curlPost_helper "$(curl -s \
                   -w "\n%{response_code}" \
                   -X POST \
                   -H "Content-Type: application/json" \
                   -u "$IMONNIT_TWILIO_CONNECTOR_WH_USER:$IMONNIT_TWILIO_CONNECTOR_WH_PASS" \
                   -d "$1" \
                   "$route"
                  )" "$2" "$3"
}


# Checks state of serverPID against R|S|D 
checkState(){
  # shellcheck disable=SC2009 # alpine pgrep does not work with pid
  state=$(ps -o pid,stat | grep " $serverPID " | awk 'NR==1 {print $2}')
  if [ "$state" = "R" ] || [ "$state" = "S" ] || [ "$state" = "D" ]; then
    return 0
  fi

  return 1
}


# Runs server.py in background. Sets global serverPID
backgroundApp(){
  if ! checkState; then
    (flask --app "$serverPath" run --host localhost --port "$IMONNIT_TWILIO_CONNECTOR_PORT") &
    serverPID=$!
    sleep 3
  fi
}


# Kills background server.py. Clears global serverPID
killApp(){
  if checkState; then
    kill -1 "$serverPID"
    serverPID=
  fi
}


# Compares server.py return value $1 for critical tests.
# Waits up to 15 sec for server.py to quit; exits tests if not and kills server.py
testAppReturn(){
  if checkState; then
    echo "[TEST] Server still running. Waiting..."
    sleep 15
    
    if checkState; then
      echo "[TEST] TEST FAILED: server did not exit."
      echo "[TEST] Killing server and stopping tests..."
      kill -1 "$serverPID" 
      serverPID=
      restoreEnv
      exit 1
    fi
  fi

  wait "$serverPID"
  serverReturnCode=$?
  if [ "$serverReturnCode" != "$1" ]; then
    printf "[TEST] Server did not exit with expected code:\n  Expected: %s\n  Got: %s\n" "$1" "$serverReturnCode"
    restoreEnv
    exit 1
  else
    echo "[TEST] Passed!"
  fi
}


# Main
echo "######################################################"
echo "######################################################"
echo "################# Starting Tests #####################"
echo "######################################################"
echo "######################################################"

# Test 1. Bad settings (missing required env variable)
setupEnv
unset MARIADB_PASSWORD
echo "[TEST] Testing bad settings..."
backgroundApp
testAppReturn 1

# Test 2. Bad db connection (bad credentials)
setupEnv
export MARIADB_PASSWORD=badPass
echo "[TEST] Testing bad db connection..."
backgroundApp
testAppReturn 2

# Test 3. No credentials
# Test 4. No rule (invalid post data) and no recipients
# Test 5. No recipients
setupEnv
unset TWILIO_PHONE_RCPTS
backgroundApp
echo "[TEST] Testing no POST credentials..."
curlPost "" "Unauthorized" 401
echo "[TEST] Testing invalid data without recipients..."
curlPostWithAuth '{"blah":"blah"}' "Unexpected Data" 400
echo "[TEST] Testing no recipients..."
# should add to db: INSERT INTO Event (Rule, Device, MessageNumber) VALUES ("Test", "no recipients", 0);
curlPostWithAuth '{"rule":"Test", "name":"no recipients"}' "" 200
killApp

# Test 6. No rule (invalid post data) with "good" recipients
setupEnv
backgroundApp
echo "[TEST] Testing invalid data with recipients..."
# Should send sms with twilio: "Error: Received bad data from iMonnit Webhook!"
curlPostWithAuth '{"blah":"blah"}' "Unexpected Data" 400
killApp

# Test 7. "Good" recipients but bad from number
setupEnv
export TWILIO_PHONE_SRC="+1aaabbbcccc"
backgroundApp
echo "[TEST] Testing bad Twilio from number..."
curlPostWithAuth '{"rule":"Test", "name":"bad from number"}' "Sending Twilio messages resulted in errors: 400, 400" 500
killApp

# Test 8. Everything good
setupEnv
export TWILIO_PHONE_RCPTS="+18777804236"
backgroundApp
echo "[TEST] Testing everything good..."
# should add to db: INSERT INTO Event (Rule, Subject, DeviceId, Device, Reading, TriggeredDT, ReadingDT, OriginalReadingDT,
#                   AcknowledgeUrl, MessageNumber, ParentAccount, NetworkId, Network, AccountId, AccountNumber, CompanyName)
#                   VALUES ("Test", "Test subject", 56789, "Everything good", "Battery: 10%", 2022-04-28 14:21:00,
#                   2022-04-28 14:20:00, 2022-04-27 14:20:00, "https://staging.imonnit.com/Ack/1234", 1, NULL, 4567,
#                   "Test Network", 123456, "Example Account", "Example Company")
# should add to db: INSERT INTO Message (EventId, MessageId, Recipient, Status) VALUES (<matching above event id>, <SMxxxx...>,
#                   "+18777804236", "queued")
# should send sms with twilio: "Test triggered by Everything good (56789)
#                               Time: 2022-04-28 14:21
#                               Reading: Battery: 10%
#                               Acknowledge: https://staging.imonnit.com/Ack/1234"
curlPostWithAuth "@${testScriptPath}/iMonnitDataExample.json" "" "200"
killApp

# Cleanup
restoreEnv
echo "[TEST] Done!"
