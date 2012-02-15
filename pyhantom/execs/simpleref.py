import os
import sys
import tempfile
from wsgiref.simple_server import make_server
from pyhantom.main_router import MainRouter

def _make_the_config_file(hostname):
    (osf, pwfile) = tempfile.mkstemp(prefix="/tmp/phantom")
    os.close(osf)
    fptr = open(pwfile, "w")
    fptr.write(os.environ['RABBITMQ_USERNAME'] + '\n')
    fptr.write(os.environ['RABBITMQ_PASSWORD'] + '\n')
    fptr.close()

    (osf, conffile) = tempfile.mkstemp(prefix="/tmp/phantomConf")
    os.close(osf)
    (osf, dbfile) = tempfile.mkstemp(prefix="/tmp/phantomDB")
    os.close(osf)

    fptr = open(conffile, "w")
    fptr.write('phantom:\n')
    fptr.write('  authz:\n')
    fptr.write('    type: simple_file\n')
    fptr.write('    filename: %s\n' % (pwfile))
    fptr.write('  system:\n')
    fptr.write('    type: epu_localdb\n')
    fptr.write('    db_url: sqlite:///%s\n' % (dbfile))
    fptr.write('    broker: %s\n' % (hostname))
    fptr.write('    rabbit_user: %s\n' % (os.environ['RABBITMQ_USERNAME']))
    fptr.write('    rabbit_pw: %s\n' % (os.environ['RABBITMQ_PASSWORD']))
    fptr.write('    rabbit_exchange: %s\n' % (os.environ['EXCHANGE_SCOPE']))
    fptr.close()
    os.environ['PHANTOM_CONFIG'] = conffile

def main(argv=sys.argv):

    hostname = argv[1]
    _make_the_config_file(hostname)

    srv = make_server('localhost', 8081, MainRouter())
    print srv.server_port
    srv.serve_forever()

    return 0

if __name__ == '__main__':
    rc = main()
    sys.exit(rc)
