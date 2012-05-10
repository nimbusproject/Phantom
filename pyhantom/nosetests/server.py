from threading import Thread
from wsgiref.simple_server import make_server
import tempfile
import os
import uuid
import time
from pyhantom.main_router import MainRouter

class BaseServer(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.username = str(uuid.uuid4()).split('-')[0]
        self.password = str(uuid.uuid4()).split('-')[0]
        self.is_ready = False

    def run(self):
        try:
            self._srv = make_server('localhost', 0, MainRouter())
            self._srv.serve_forever()
            self.is_ready = True
        except Exception, ex:
            print "failed to start the server %s" % (str(ex))
            raise

    def get_boto_values(self):
        return (self.username, self.password, self._srv.server_address[0], self._srv.server_address[1])

    def end(self):
        self._srv.shutdown()
        os.remove(self.conffile)
        os.remove(self.pwfile)


class RunPwFileServer(BaseServer):

    def __init__(self):
        BaseServer.__init__(self)
        (osf, self.pwfile) = tempfile.mkstemp(prefix="/tmp/phantom")
        os.close(osf)
        fptr = open(self.pwfile, "w")
        fptr.write(self.username + ' ' + self.password + '\n')
        fptr.close()

        (osf, self.conffile) = tempfile.mkstemp(prefix="/tmp/phantom")
        os.close(osf)
        fptr = open(self.conffile, "w")
        fptr.write('phantom:\n')
        fptr.write('  authz:\n')
        fptr.write('    type: simple_file\n')
        fptr.write('    filename: %s\n' % (self.pwfile))
        fptr.write('  system:\n')
        fptr.write('    type: tester\n')
        fptr.close()
        os.environ['PHANTOM_CONFIG'] = self.conffile



class RunPwFileEPUServer(BaseServer):

    def __init__(self, db_url):
        BaseServer.__init__(self)
        (osf, self.pwfile) = tempfile.mkstemp(prefix="/tmp/phantom")
        os.close(osf)
        fptr = open(self.pwfile, "w")
        fptr.write(self.username + ' ' + self.password + '\n')
        fptr.close()

        (osf, self.conffile) = tempfile.mkstemp(prefix="/tmp/phantom")
        os.close(osf)
        fptr = open(self.conffile, "w")
        fptr.write('phantom:\n')
        fptr.write('  authz:\n')
        fptr.write('    type: simple_file\n')
        fptr.write('    filename: %s\n' % (self.pwfile))
        fptr.write('  system:\n')
        fptr.write('    type: localdb\n')
        fptr.write('    db_url: %s\n' % (db_url))
        fptr.close()
        os.environ['PHANTOM_CONFIG'] = self.conffile
