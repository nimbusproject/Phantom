#!/usr/bin/env python

import sys
import os
import subprocess
import tempfile

userpattern=sys.argv[1]
nh=os.environ['NIMBUS_HOME']
phantomkey_name="phantomkey"

cmd = ["%s/bin/nimbus-list-users" % (nh),  "-b", "-r", "access_id,access_secret,display_name",  "%s" % (userpattern)]

cei_cmd="%s/bin/ceictl -b %s -x %s -u %s -p %s " % (os.environ['PHANTOM_CEICTL_DIR'], os.environ['PHANTOM_EPU_RABBIT_HOST'], os.environ['EXCHANGE_SCOPE'], os.environ['RABBITMQ_USERNAME'], os.environ['RABBITMQ_PASSWORD'])

p = subprocess.Popen(cmd, stdout=subprocess.PIPE)

for line in p.stdout.readlines():
    l_a = line.strip().split(',')
    access_key = l_a[0]
    access_secret = l_a[1]
    display_name = l_a[2]

    print "%s %s %s" % (display_name, access_key, access_secret)
    (osf, fname) = tempfile.mkstemp()

    os.write(osf, "access_key: %s\n" % (access_key))
    os.write(osf, "access_secret: %s\n" % (access_secret))
    os.write(osf, "key_name: %s\n" % (phantomkey_name))
    os.close(osf)

    cmd="%s credentials add --definition %s" % (cei_cmd, fname)

    print cmd

    os.remove(fname)

