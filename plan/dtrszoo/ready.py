#!/home/epu/app-venv/bin/python

import uuid
import time
import uuid
import json
import sys
from epu.dashiproc.dtrs import DTRS, DTRSClient
import dashi.bootstrap as bootstrap

def main():
    f = open("bootconf.json", "r")
    conf_dict = json.load(f)

    rabbitmq_conf = conf_dict['epu']["run_config"]["config"]["server"]["amqp"]
    rabbitmq_host = rabbitmq_conf["host"]
    rabbitmq_username = rabbitmq_conf["username"]
    rabbitmq_password = rabbitmq_conf["password"]

    client_topic = "dtrs_client_%s" % uuid.uuid4()


    uri = "amqp://%s:%s@%s" % (rabbitmq_username, rabbitmq_password, rabbitmq_host)
    client_dashi = bootstrap.dashi_connect(client_topic, amqp_uri=uri)

    dtrs_client = DTRSClient(dashi=client_dashi)
    for i in range(0, 3):
        try:
            sites = dtrs_client.list_sites()
            print sites
            break
        except Exception, ex:
            print ex
            time.sleep(5);

    # if we passed check one more time to avoid a fluke.  If we failed give 
    # a brubbah one more shot at glory
    sites = dtrs_client.list_sites()
    print sites
    return 0

rc = main()
sys.exit(rc)

