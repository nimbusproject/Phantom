from threading import Thread
from wsgiref.simple_server import make_server
import tempfile
import os
import uuid
from pyhantom.main_router import MainRouter

class RunTestPwFileServer(Thread):

    def __init__(self, app):
        Thread.__init__(self)
        self._app = app
        (osf, self.pwfile) = tempfile.mkstemp(prefix="/tmp/phantom")
        os.close(osf)
        self.username = str(uuid.uuid4()).split('-')[0]
        self.password = str(uuid.uuid4()).split('-')[0]
        fptr = open(self.pwfile, "w")
        fptr.write(self.username + '\n')
        fptr.write(self.password + '\n')
        fptr.close()

        (osf, self.conffile) = tempfile.mkstemp(prefix="/tmp/phantom")
        os.close(osf)
        fptr = open(self.conffile, "w")
        fptr.write('phantom:\n')
        fptr.write('  authz:\n')
        fptr.write('    type: simple_file\n')
        fptr.write('    filename: %s\n' % (self.pwfile))
        fptr.close()
        os.environ['PHANTOM_CONFIG'] = self.conffile

    def run(self):
        try:
            self._srv = make_server('localhost', 0, MainRouter())
            self._srv.serve_forever()
        except Exception, ex:
            print "failed to start the server %s" % (str(ex))

    def get_boto_values(self):
        return (self.username, self.password, self._srv.server_port)

    def end(self):
        self._srv.shutdown()
        os.remove(self.conffile)
        os.remove(self.pwfile)
