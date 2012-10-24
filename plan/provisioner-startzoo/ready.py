#!/home/epu/app-venv/bin/python

import time
import uuid
import json
import sys
import dashi.bootstrap as bootstrap
from epu.dashiproc.provisioner import ProvisionerClient

def main():
    f = open("bootconf.json", "r")
    conf_dict = json.load(f)

    rabbitmq_conf = conf_dict['epu']["run_config"]["config"]["server"]["amqp"]
    rabbitmq_host = rabbitmq_conf["host"]
    rabbitmq_username = rabbitmq_conf["username"]
    rabbitmq_password = rabbitmq_conf["password"]

    rabbitmq_exchange = "default_dashi_exchange"

    uri = "amqp://%s:%s@%s" % (rabbitmq_username, rabbitmq_password, rabbitmq_host)

    client_topic = "provisioner_client_%s" % uuid.uuid4()
    client_dashi = bootstrap.dashi_connect(client_topic, amqp_uri=uri)
    client = ProvisionerClient(client_dashi)
    for i in range(0, 3):
        try:
            x = client.describe_nodes(caller="HTEdNFYDys8RdP")
            print x
            break
        except Exception, ex:
            print ex
            time.sleep(5);

    # if we passed check one more time to avoid a fluke.  If we failed give 
    # a brubbah one more shot at glory
    x = client.describe_nodes(caller="HTEdNFYDys8RdP")
    print x
    return 0

rc = main()
sys.exit(rc)
