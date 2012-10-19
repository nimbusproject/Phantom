#!/bin/bash

set -e

APP_DIR=`cat bootconf.json | python -c "import sys; import json; j = json.loads(sys.stdin.read()); print j['epu']['run_config']['run_directory']"`
PROCESS_NAME=`cat bootconf.json | python -c "import sys; import json; j = json.loads(sys.stdin.read()); print j['epu']['run_config']['program']"`
VENV_PATH=`cat bootconf.json | python -c "import sys; import json; j = json.loads(sys.stdin.read()); print j['epu']['virtualenv']['path']"`

set +e
STATUS=`sudo -u epu sh -c ". $VENV_PATH/bin/activate; supervisorctl -c $APP_DIR/supervisor.conf status"`
echo $STATUS | grep $PROCESS_NAME | grep RUNNING > /dev/null
if [ $? != 0 ]; then
  echo $STATUS
  exit 1
fi
