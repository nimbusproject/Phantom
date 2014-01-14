#!/home/epu/app-venv/bin/python

import uuid
import json
import sys

from epu.dashiproc.epumanagement import EPUManagementClient
import dashi.bootstrap as bootstrap

def main():
    f = open("bootconf.json", "r")
    conf_dict = json.load(f)

    rabbitmq_conf = conf_dict['epu']["run_config"]["config"]["server"]["amqp"]
    rabbitmq_host = rabbitmq_conf["host"]
    rabbitmq_username = rabbitmq_conf["username"]
    rabbitmq_password = rabbitmq_conf["password"]

    rabbitmq_exchange = "default_dashi_exchange"

    uri = "amqp://%s:%s@%s" % (rabbitmq_username, rabbitmq_password, rabbitmq_host)

    client_topic = "epum_client_%s" % uuid.uuid4()
    client_dashi = bootstrap.dashi_connect(client_topic, amqp_uri=uri)
    epum_client = EPUManagementClient(client_dashi, 'epu_management_service')
    defs = epum_client.list_domain_definitions()
    print defs

    return 0

rc = main()
sys.exit(rc)

