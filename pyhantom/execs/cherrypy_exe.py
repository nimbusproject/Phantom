import os
import sys
from cherrypy import wsgiserver
from pyhantom.main_router import MainRouter

def usage():
    print "<path to config file> <port>"
    sys.exit(1)

def main(argv=sys.argv):

    if len(argv) < 3:
        usage()

    conf_file = argv[1]
    if not os.path.exists(conf_file):
        print "The file %s does not exist" % (conf_file)
        usage()

    try:
        port = int(argv[2])
    except Exception, ex:
        print "you must supply a server port number"
        usage()

    server = wsgiserver.CherryPyWSGIServer(
            ('0.0.0.0', port), MainRouter,
            server_name='phantom')
    server.start()


    return 0

if __name__ == '__main__':
    rc = main()
    sys.exit(rc)
