#!/usr/bin/env python

# this program is useful for adding certs to the test environment

import sys
import os
import subprocess
from ceiclient.client import DTRSClient
from ceiclient.connection import DashiCeiConnection
import boto
import urlparse
from pyhantom.config import build_cfg
import boto
from boto.ec2.regioninfo import RegionInfo
from phantomsql import phantom_get_default_key_name


def get_dashi_client():

    ssl = False
    rabbit = os.environ['PHANTOM_EPU_RABBIT_HOST']
    rabbit_port = 5672
    rabbitpw = os.environ['RABBITMQ_PASSWORD']
    rabbituser = os.environ['RABBITMQ_USERNAME']
    rabbitexchange = os.environ['EXCHANGE_SCOPE']
    dashi_conn = DashiCeiConnection(rabbit, rabbituser, rabbitpw, exchange=rabbitexchange, timeout=60, port=rabbit_port, ssl=ssl)
    return dashi_conn

def get_user_public_key():
    f = open(os.path.expanduser("~/.ssh/id_rsa.pub"))
    lines = list(f.readlines())
    k = ''.join(lines)
    return k.strip()

def register_key_with_iaas(iaas_url, keytext, keyname, access_key, access_secret):

    up = urlparse.urlparse(iaas_url)

    ssl = up.scheme == "https"
    host = up.hostname
    port = up.port

    region = RegionInfo(name="nimbus", endpoint=host)
    ec2conn = boto.connect_ec2(access_key, access_secret, region=region, port=port)
    ec2conn.import_key_pair(keyname, keytext)


def add_one_user(dtrs_client, access_key, access_secret, pub_key, email, username):
    phantomkey_name = phantom_get_default_key_name()
    creds = {'access_key': access_key,
            'secret_key': access_secret,
            'key_name': phantomkey_name}

    hosts = {"hotel": "https://svc.uc.futuregrid.org:8444", "sierra" : "https://s83r.idp.sdsc.futuregrid.org:8444", "alamo": "https://master1.futuregrid.tacc.utexas.edu:8444", "foxtrot": "https://f1r.idp.ufl.futuregrid.org:9444"}
    print "public key is %s" % (pub_key)
    for host in hosts:
        dtrs_client.add_credentials(access_key, host, creds)
        register_key_with_iaas(hosts[host], pub_key, phantomkey_name, access_key, access_secret)

def main():

    if len(sys.argv) != 5:
        print "usage: add_users <user pattern> <nimbus home> <phantom conf file>"
        sys.exit(1)

    name = sys.argv[1]
    access_key = sys.argv[2]
    access_secret = sys.argv[3]
    email = sys.argv[4]
    ssh_key = get_user_public_key()

    dashi_con = get_dashi_client()
    dtrs_client = DTRSClient(dashi_con)
    add_one_user(dtrs_client, access_key, access_secret, ssh_key, email, name)

if __name__ == '__main__':
    rc = main()
    sys.exit(rc)
