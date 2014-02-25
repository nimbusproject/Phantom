#!/usr/bin/env python

import sys
import os
import json

f = open("bootconf.json", "r")
vals_dict = json.load(f)
f.close()

os.putenv('DEBIAN_FRONTEND', 'noninteractive')
os.putenv('TERM', 'dumb')

password=vals_dict['dbpassword']
dbname=vals_dict['dbname']
webdbname=vals_dict['webdbname']
dbuser=vals_dict['dbuser']

commands = []
commands.append('sudo -E apt-get -y update')
commands.append('sudo -E apt-get -y -q install mysql-server')
commands.append('sudo -E mysqladmin -u root password %s' % (password))
commands.append('sudo -E mysqladmin --password=%s create %s' % (password, dbname))
commands.append('sudo -E mysqladmin --password=%s create %s' % (password, webdbname))
commands.append("sudo -E mysql --password=%s -e \"GRANT INDEX, Select, Insert, Update, Create, Delete, Alter ON *.* TO '%s'@'%%' IDENTIFIED BY '%s';\"" % (password, dbuser, password))
commands.append("sudo -E sed -i 's/bind-address.*/bind-address = 0.0.0.0/' /etc/mysql/my.cnf")
commands.append("sudo -E service mysql restart")

for cmd in commands:
    print cmd
    rc = os.system(cmd)
    if rc != 0:
        if os.WIFEXITED(rc):
            rc = os.WEXITSTATUS(rc)
            print "ERROR! %d" % (rc)
        else:
            print "UNKNOWN EXIT! %d" % (rc)
        sys.exit(rc)

print "SUCCESS"
sys.exit(0)
