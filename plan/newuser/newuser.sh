#!/bin/bash

set -e

source bootconf.json

cd /home/epu/phantom/sandbox/FG
if [ ! -f /home/epu/.ssh/id_rsa ]; then
    sudo -E -H -u epu bash -c "ssh-keygen -f /home/epu/.ssh/id_rsa -N ''"
fi

export PYTHON_EGG_CACHE=/tmp/python-eggs-epu
sudo -E -H -u epu bash -c "source /home/epu/app-venv/bin/activate && ./add_sites.sh"
sudo -E -H -u epu bash -c "source /home/epu/app-venv/bin/activate && ./test_add_user.py $PHANTOM_USERNAME $PHANTOM_IAAS_ACCESS_KEY $PHANTOM_IAAS_SECRET_KEY"
sudo -E -H -u epu bash -c "source /home/epu/app-venv/bin/activate && ./add_mysql_user.py $PHANTOM_USERNAME $PHANTOM_IAAS_ACCESS_KEY $PHANTOM_IAAS_SECRET_KEY /home/epu/phantom/phantomautoscale.yml"

cd /home/epu/phantomweb
export PYTHON_EGG_CACHE=/tmp/python-eggs-www-data
sudo -E -H -u www-data bash -c "./bin/phantomweb-new-user.py $PHANTOM_USERNAME $PHANTOM_USER_EMAIL $PHANTOM_IAAS_ACCESS_KEY $PHANTOM_IAAS_SECRET_KEY"
