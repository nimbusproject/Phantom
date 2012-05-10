#!/usr/bin/env python

import sys
import os
import subprocess
import tempfile
from pyhantom.execs.add_user import add_user
from ceiclient.client import DTRSCredentialsClient
from pyhantom.config import build_cfg
from pyhantom.util import get_default_keyname


def get_dashi_client(cfg):
    ssl = cfg.phantom.system.rabbit_ssl
    rabbit = cfg.phantom.system.rabbit
    rabbit_port = cfg.phantom.system.rabbit_port
    rabbitpw = cfg.phantom.system.rabbit_pw
    rabbituser = cfg.phantom.system.rabbit_user
    rabbitexchange = cfg.phantom.system.rabbit_exchange
    dashi_conn = DashiCeiConnection(rabbit, rabbituser, rabbitpw, exchange=rabbitexchange, timeout=60, port=rabbit_port, ssl=ssl)
    return dashi_conn


def get_fg_users(userpattern, nh):
    cmd = ["%s/bin/nimbus-list-users" % (nh),  "-b", "-r", "display_name,access_id,access_secret",  "%s" % (userpattern)]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    user_pw_list = []
    for line in p.stdout.readlines():
        l_a = line.strip().split(',')        
        user_pw_list.append(l_a)


def main():
    userpattern=sys.argv[1]
    nh=os.environ['NIMBUS_HOME']

    user_pw_list = get_fg_users(userpattern, nh)
    cfg = build_cfg()

    dashi_con = get_dashi_client(cfg)
    cred_client = DTRSCredentialsClient(dashi_con)

    phantomkey_name = get_default_keyname()
    for (name, access_key, access_secret) in user_pw_list:
        creds = {'access_key': access_key,
                    'secret_key': access_secret,
                    'key_name': phantomkey_name}

        hosts = ["hotel", "sierra", "alamo", "foxtrot"]
        for host in hosts:
            cred_client.add_credentials(access_key, host, creds)
        add_user(access_key, access_secret)

if __name__ == '__main__':
    rc = main()
    sys.exit(rc)