#!/usr/bin/env python

import sys
import os
import subprocess
from ceiclient.client import DTRSCredentialsClient
import boto
import urlparse
from pyhantom.config import build_cfg
from pyhantom.util import get_default_keyname
import boto
from boto.ec2.regioninfo import RegionInfo
import urllib2

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

def get_fg_users(userpattern, nh):
    cmd = ["%s/bin/nimbus-list-users" % (nh),  "-b", "-r", "display_name,access_id,access_secret",  "%s" % (userpattern)]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    user_pw_list = []
    for line in p.stdout.readlines():
        l_a = line.strip().split(',')
        user_pw_list.append(l_a)

def get_user_public_key(username):
    ldapbasedn = "dc=futuregrid,dc=org"
    ldapfilter = "(&(objectclass=ldapPublicKey)(cn=%s))" % (sys.argv[1])
    ldapattribs = ['sshPublicKey']
    ldapscope = ldap.SCOPE_SUBTREE

    l = ldap.open("ldap.futuregrid.org")
    l.simple_bind_s()

    ldapresults = l.search_s(ldapbasedn, ldapscope, ldapfilter, ldapattribs)
    res = ldapresults[0]
    return res[1]['sshPublicKey'][0]

def register_key_with_iaas(iaas_url, keytext, keyname, access_key, access_secret):

    up = urlparse.urlparse(iaas_url)

    ssl = up.scheme == "https"
    host = up.hostname
    port = up.port

    region = RegionInfo(name="nimbus", endpoint=host)
    ec2conn = boto.connect_ec2(access_key, access_secret, region=region, port=port)
    #keytext = base64.b64encode(keytext)
    ec2conn.import_key_pair(keyname, keytext)


def main():

    if len(sys.argv) != 4:
        print "usage: add_users <user pattern> <nimbus home> <phantom conf file>"
        sys.exit(1)
    userpattern=sys.argv[1]
    nh=sys.argv[2]
    os.environ['PHANTOM_CONFIG'] = sys.argv[3]

    user_pw_list = get_fg_users(userpattern, nh)
    cfg = build_cfg()
    authz = cfg.get_authz()

    dashi_con = get_dashi_client(cfg)
    cred_client = DTRSCredentialsClient(dashi_con)

    phantomkey_name = get_default_keyname()
    for (name, access_key, access_secret) in user_pw_list:
        print "handling user %s" % (name)
        creds = {'access_key': access_key,
                    'secret_key': access_secret,
                    'key_name': phantomkey_name}

        hosts = {"hotel": "https://svc.uc.futuregrid.org:8444", "sierra" : "https://s83r.idp.sdsc.futuregrid.org:8444", "alamo": "https://master1.futuregrid.tacc.utexas.edu:8444", "foxtrot": "https://f1r.idp.ufl.futuregrid.org:9444"}
        ssh_key = get_user_public_key(name)
        print "public key is %s" % (ssh_key)
        for host in hosts:
            cred_client.add_credentials(access_key, host, creds)
            register_key_with_iaas(hosts[host], ssh_key, phantomkey_name, access_key, access_secret)

        authz.add_user(access_key, access_secret)

if __name__ == '__main__':
    rc = main()
    sys.exit(rc)