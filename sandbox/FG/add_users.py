#!/usr/bin/env python

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
import ldap
import dashi

def phantom_get_default_key_name():
    return "phantomkey"

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
    return user_pw_list

def get_user_public_key(username):
    ldapbasedn = "dc=futuregrid,dc=org"
    ldapfilter = "(&(objectclass=ldapPublicKey)(cn=%s))" % (username)
    ldapattribs = ['sshPublicKey', 'mail']
    ldapscope = ldap.SCOPE_SUBTREE
    l = ldap.open("ldap.futuregrid.org")
    l.simple_bind_s()
    ldapresults = l.search_s(ldapbasedn, ldapscope, ldapfilter, ldapattribs)
    res = ldapresults[0]
    pubkey = res[1]['sshPublicKey'][0]
    email = res[1]['mail'][0]
    return (email, pubkey)

def register_key_with_iaas(iaas_url, keytext, keyname, access_key, access_secret):

    up = urlparse.urlparse(iaas_url)

    ssl = up.scheme == "https"
    host = up.hostname
    port = up.port

    region = RegionInfo(name="nimbus", endpoint=host)
    ec2conn = boto.connect_ec2(access_key, access_secret, region=region, port=port, validate_certs=False)

    # Workaround for a bug in Nimbus <= 2.10.1:
    # import_key_pair does not properly update an existing key
    try:
        if ec2conn.get_key_pair(keyname) is not None:
            ec2conn.delete_key_pair(keyname)
    except IndexError:
        # This exception is raised when boto can't find a key on Nimbus
        pass
    ec2conn.import_key_pair(keyname, keytext)


def add_one_user(authz, dtrs_client, access_key, access_secret, pub_key, email, username):
    phantomkey_name = phantom_get_default_key_name()
    creds = {'access_key': access_key,
            'secret_key': access_secret,
            'key_name': phantomkey_name}

    hosts = {"hotel": "https://svc.uc.futuregrid.org:8444", "alamo": "https://nimbus.futuregrid.tacc.utexas.edu:8444", "foxtrot": "https://f1r.idp.ufl.futuregrid.org:9444"}
    print "public key is %s" % (pub_key)
    for host in hosts:
        try:
            dtrs_client.add_credentials(access_key, host, creds)
        except dashi.exceptions.DashiError:
            print "Failed to add credentials for site %s" % host
            pass

        print "Adding key %s to cloud %s" % (phantomkey_name, hosts[host])
        register_key_with_iaas(hosts[host], pub_key, phantomkey_name, access_key, access_secret)

    authz.add_user(username, access_key, access_secret)

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

    dashi_con = get_dashi_client(cfg._CFG)
    dtrs_client = DTRSClient(dashi_con)

    for (name, access_key, access_secret) in user_pw_list:
        print "handling user %s" % (name)
        (email, ssh_key) = get_user_public_key(name)
        add_one_user(authz, dtrs_client, access_key, access_secret, ssh_key, email, name)

if __name__ == '__main__':
    rc = main()
    sys.exit(rc)
