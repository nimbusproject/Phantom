#!/usr/bin/env python

# this program is useful for adding certs to the test environment

import sys
import os
import socket
import subprocess
from ceiclient.client import DTRSClient
from ceiclient.connection import DashiCeiConnection
import boto
import urlparse
from pyhantom.config import build_cfg
import boto
from boto.ec2.regioninfo import RegionInfo

def phantom_get_default_key_name():
    return "phantomkey"

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

    print "Registering key %s with %s" % (keyname, iaas_url)

    region = RegionInfo(name="nimbus", endpoint=host)
    ec2conn = boto.connect_ec2(access_key, access_secret, region=region, port=port, is_secure=True, validate_certs=False)
    ec2conn.import_key_pair(keyname, keytext)


def add_one_user(dtrs_client, access_key, access_secret, pub_key, username):
    phantomkey_name = phantom_get_default_key_name()
    creds = {'access_key': access_key,
            'secret_key': access_secret,
            'key_name': phantomkey_name}

    hosts = {"hotel": "https://svc.uc.futuregrid.org:8444", "alamo": "https://nimbus.futuregrid.tacc.utexas.edu:8444", "foxtrot": "https://f1r.idp.ufl.futuregrid.org:9444"}
    print "public key is %s" % (pub_key)
    for host in hosts:
        try:
            dtrs_client.add_credentials(access_key, host, creds)
        except:
            pass
        try:
            register_key_with_iaas(hosts[host], pub_key, phantomkey_name, access_key, access_secret)
        except socket.timeout:
            print "Error: timeout when registering key %s on %s" % (phantomkey_name, host)
            pass
        except socket.error:
            print "Error: socket error when registering key %s on %s" % (phantomkey_name, host)
            pass

def main():

    if len(sys.argv) != 4:
        print "usage: test_add_user name access_key access_secret"
        sys.exit(1)

    name = sys.argv[1]
    access_key = sys.argv[2]
    access_secret = sys.argv[3]
    ssh_key = get_user_public_key()

    if not boto.config.has_section('Boto'):
        boto.config.add_section('Boto')
    boto.config.set('Boto', 'http_socket_timeout', '10')
    boto.config.set('Boto', 'num_retries', '3')

    dashi_con = get_dashi_client()
    dtrs_client = DTRSClient(dashi_con)
    add_one_user(dtrs_client, access_key, access_secret, ssh_key, name)

if __name__ == '__main__':
    rc = main()
    sys.exit(rc)
