#!/usr/bin/env python
import simplejson as json
import sys
import os
import shutil

try:
    inf = open("bootconf.json", "r")
    pyd = json.load(inf)

    pwfname = pyd['phantom']['authz']['filename']
    users = pyd['cloudinitdonly']['users']
    outfpw = open(pwfname, "w")
    for u in users:
        line = "%s %s\n" % (u, users[u])
        outfpw.write(line)
    outfpw.close()

    homedir = pyd['cloudinitdonly']['homedir']
    outfname = "%s/phantomconf.json" % (homedir)
    outf = open(outfname, "w")

    del pyd['cloudinitdonly']
    json.dump(pyd, outf, indent='    ')

    cert_dst = "%s/phantomcert.pem" % (homedir)
    key_dst = "%s/phantomkey.pem" % (homedir)
    shutil.copy("/etc/ssl/rabbitmq/server/cert.pem", cert_dst)
    shutil.copy("/etc/ssl/rabbitmq/server/key.pem", key_dst)

    chown_files = [key_dst, cert_dst, "%s/phantom_pwfile" % (homedir), "%s/phantomconf.json" % (homedir)]
    for f in chown_files:
        os.chmod(f, 0600)
        os.system("chown epu:users %s" % (f))

    sys.exit(0)
finally:
    pass
    # for security reasons we will want to clean that up
    #os.remove(bootconf.json)
