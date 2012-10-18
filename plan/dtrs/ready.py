#!/usr/bin/env python

import simplejson as json
import sys
from epu.dashiproc.dtrs import DTRS, DTRSClient

def main():
    f = open("bootconf.json", "r")
    conf_dict = json.load(f)

    rabbitmq_conf = conf_dict['epu']["run_config"]["config"]["server"]["amqp"]
    rabbitmq_host = rabbitmq_conf["host"]
    rabbitmq_username = rabbitmq_conf["username"]
    rabbitmq_password = rabbitmq_conf["password"]

    rabbitmq_exchange = "default_dashi_exchange"

    uri = "amqp://%s:%s@%s" % (rabbitmq_username, rabbitmq_password, rabbitmq_host)
    dtrs = DTRS(amqp_uri=uri)
    dtrs_client = DTRSClient(dashi=dtrs.dashi)
    sites = dtrs_client.list_sites()
    print sites

    return 0

rc = main()
sys.exit(rc)
