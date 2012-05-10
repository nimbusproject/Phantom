import os
import simplejson as json
import tempfile
import sys


def make_conf(cid_out_filename, conffile, localdb_fname, pwfile,  pwfile_type="simple_file", logfile="/tmp/phantom.log"):
    fptr = open(cid_out_filename, "r")
    j = json.load(fptr)

    baseservice = j['levels'][0]['services'][0]

    xchg = baseservice['exchange_scope']
    username = baseservice['rabbitmq_username']
    pw = baseservice['rabbitmq_password']
    hostname = baseservice['hostname']

    fptr = open(conffile, "w")
    fptr.write('phantom:\n')
    fptr.write('  authz:\n')
    fptr.write('    type: %s\n' % (pwfile_type))
    fptr.write('    dburl: %s\n' % (pwfile))
    fptr.write('  system:\n')
    fptr.write('    type: epu_localdb\n')
    fptr.write('    db_url: sqlite:///%s\n' % (localdb_fname))
    fptr.write('    rabbit_hostname: %s\n' % (hostname))
    fptr.write('    rabbit_user: %s\n' % (username))
    fptr.write('    rabbit_pw: %s\n' % (pw))
    fptr.write('    rabbit_exchange: %s\n' % (xchg))

    fptr.write('logging:\n')
    fptr.write('  handlers:\n')
    fptr.write('    file:\n')
    fptr.write('      filename: %s\n' % (logfile))

    fptr.close()


def main(argv=sys.argv):

    if len(argv) != 4:
        print "usage"
        print "<output file from cloudinitd> <phantom database file> <cumulus authz file>"
        return 1

    cid_file = argv[1]
    db_file = argv[2]
    pwfile = argv[2]
    
    (osf, conffile) = tempfile.mkstemp(prefix="/tmp/phantomConf")
    os.close(osf)

    make_conf(cid_file, conffile, db_file, pwfile, pwfile_type="cumulus")

    print conffile

    return 0

if __name__ == '__main__':
    rc = main()
    sys.exit(rc)
