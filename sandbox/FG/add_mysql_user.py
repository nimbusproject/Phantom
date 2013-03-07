#!/usr/bin/env python

import os
import sys

from pyhantom.config import build_cfg


def main():

    if len(sys.argv) != 5:
        print "usage: add_mysql_user <username> <key> <secret> <path to conf>"
        sys.exit(1)
    username = sys.argv[1]
    access_key = sys.argv[2]
    access_secret = sys.argv[3]
    os.environ['PHANTOM_CONFIG'] = sys.argv[4]

    cfg = build_cfg()
    authz = cfg.get_authz()

    authz.add_user(username, access_key, access_secret)

if __name__ == '__main__':
    rc = main()
    sys.exit(rc)
