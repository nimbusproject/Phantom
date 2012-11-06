#!/usr/bin/env python

import os
import subprocess
import sys
import urlparse

import boto
from boto.ec2.regioninfo import RegionInfo
from phantomsql import phantom_get_default_key_name

from pyhantom.config import build_cfg


def main():

    if len(sys.argv) != 6:
        print "usage: add_mysql_user <username> <email> <key> <secret> <path to conf>"
        sys.exit(1)
    username = sys.argv[1]
    email = sys.argv[2]
    access_key = sys.argv[3]
    access_secret = sys.argv[4]
    os.environ['PHANTOM_CONFIG'] = sys.argv[5]

    cfg = build_cfg()
    authz = cfg.get_authz()

    authz.add_user(username, access_key, access_secret)

if __name__ == '__main__':
    rc = main()
    sys.exit(rc)
