#!/bin/bash

thisdir=`dirname $0`
sites="alamo-openstack alamo ec2-eu ec2 foxtrot hotel hotel-openstack india-openstack sierra-openstack sierra"

if [ -z $PHANTOM_EPU_RABBIT_HOST ]; then
    echo "Please setup the environment"
    exit 1
fi

for site in $sites
do
    cmd="ceictl -b $PHANTOM_EPU_RABBIT_HOST -x $EXCHANGE_SCOPE -u $RABBITMQ_USERNAME -p $RABBITMQ_PASSWORD site add $site --definition $thisdir/$site.yml"
    echo $cmd
    $cmd
done

ceictl -b $PHANTOM_EPU_RABBIT_HOST -x $EXCHANGE_SCOPE -u $RABBITMQ_USERNAME -p $RABBITMQ_PASSWORD site list
