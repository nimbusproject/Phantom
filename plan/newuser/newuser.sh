#!/bin/bash

set -e

source bootconf.json

cd /home/epu/phantom/sandbox/FG
if [ ! -f /home/epu/.ssh/id_rsa ]; then
    su epu sh -c "ssh-keygen -f /home/epu/.ssh/id_rsa -N ''"
fi

su epu sh -c "source /home/epu/app-venv/bin/activate && ./add_sites.sh"
su epu sh -c "source /home/epu/app-venv/bin/activate && ./test_add_user.py $PHANTOM_USERNAME $PHANTOM_IAAS_ACCESS_KEY $PHANTOM_IAAS_SECRET_KEY"
su epu sh -c "source /home/epu/app-venv/bin/activate && ./add_mysql_user.py $PHANTOM_USERNAME $PHANTOM_IAAS_ACCESS_KEY $PHANTOM_IAAS_SECRET_KEY /home/epu/phantom/phantomautoscale.yml"

cd /home/epu/phantomweb
su www-data sh -c "./bin/phantomweb-new-user.py $PHANTOM_USERNAME $PHANTOM_USER_EMAIL $PHANTOM_IAAS_SECRET_KEY"
