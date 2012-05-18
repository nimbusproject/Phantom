#!/bin/bash

set -e

APP_DIR=`cat bootconf.json | python -c "import sys; import json; j = json.loads(sys.stdin.read()); print j['appdir']"`
APP_NAME=`cat bootconf.json | python -c "import sys; import json; j = json.loads(sys.stdin.read()); print j['appname']"`
VENV_PATH=`cat bootconf.json | python -c "import sys; import json; j = json.loads(sys.stdin.read()); print j['virtualenv']['path']"`

set +e
STATUS=`sudo -u epu sh -c ". $VENV_PATH/bin/activate; supervisorctl -c $APP_DIR/supervisor.conf status $APP_NAME"`
echo $STATUS | grep RUNNING > /dev/null
if [ $? != 0 ]; then
  echo $STATUS
  exit 1
fi
