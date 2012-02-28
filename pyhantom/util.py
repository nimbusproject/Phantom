import base64
import boto
from hashlib import sha1
from hashlib import sha256
import boto.utils
import boto.provider
import hmac
import logging
import traceback
import urllib
import webob.exc
import datetime
from pyhantom.phantom_exceptions import PhantomAWSException, PhantomNotImplementedException

def log(lvl, message, printstack=False):
    logger = logging.getLogger("phantom")
    logger.log(lvl, message)

    if printstack:
        str = traceback.format_exc()
        logger.log(lvl, str)

def log_request(req, user_obj):
    log(logging.INFO, "Received request %s from user %s" % (str(req.params), user_obj.username))

def log_reply(doc, user_obj):
    log(logging.INFO, "Sending reply %s to user %s" % (doc.documentElement.toprettyxml(), user_obj.username))


def not_implemented_decorator(func):
    def call(self, *args,**kwargs):
        def raise_error(func):
            raise PhantomNotImplementedException("function %s must be implemented" % (func.func_name))
        return raise_error(func)
    return call

# A decorator for trapping errors in our applications
class LogEntryDecorator(object):

    def __init__(self, classname=None):
        if classname:
            self._classname = classname + ":"

    def __call__(self, func):
        def wrapped(*args, **kw):
            try:
                log(logging.DEBUG, "Entering %s%s." % (self._classname, func.func_name))
                return func(*args, **kw)
            except Exception, ex:
                log(logging.ERROR, "exiting %s%s with error: %s." % (self._classname, func.func_name, str(ex)))
                raise
            finally:
                log(logging.DEBUG, "Exiting %s%s." % (self._classname, func.func_name))
        return wrapped


# A decorator for trapping errors in our applications
class CatchErrorDecorator(object):

    def __init__(self, appname=""):
        self._app_name = appname

    def __call__(self, func):
        def wrapped(*args, **kw):
            try:
                return func(*args, **kw)
            except webob.exc.HTTPException, httpde:
                log(logging.INFO, "Application %s:%s received HTTP error %s" % (self._app_name, func.func_name, httpde), printstack=True)
                return httpde
            except Exception, ex:
                log(logging.ERROR, "Application %s:%s received Unknown error %s" % (self._app_name, func.func_name, ex), printstack=True)
                # convert to a http exception
                raise PhantomAWSException('InternalFailure', details=str(ex))
            finally:
                pass
        return wrapped

def phantom_is_primative(t):
    return t == str or t == int or t == bool or t == float or t == unicode

def get_auth_hash(key, req):
    if req.params['SignatureVersion'] == '2':
        sig = calc_v2_signature(key, req)
    elif req.params['SignatureVersion'] == '1':
        sig = calc_v1_signature(key, req)
    else:
        sig = calc_v0_signature(key, req)
    return sig

def _get_time(str_time):
    str_time = str_time.replace("Z", "UTC")
    return datetime.datetime.strptime(str_time, '%Y-%m-%dT%H:%M:%S%Z')

def make_time(datetimeobj):
    fmt = '%Y-%m-%dT%H:%M:%S.%fZ'
    dt = datetime.datetime.strftime(datetimeobj, fmt)
    return dt

def authenticate_user(req, access_key):
    access_id = req.params['AWSAccessKeyId']
    signature = req.params['Signature']

    if not access_key:
        log(logging.WARN, "The user %s was not found." % (access_id))
        raise PhantomAWSException('InvalidClientTokenId')
    proper_signature = get_auth_hash(access_key, req)

    if signature != proper_signature:
        log(logging.WARN, "The signature for user %s was not correct." % (access_id))
        raise PhantomAWSException('IncompleteSignature')

    # check the time
    expr_time = None
    nw = datetime.datetime.utcnow()
    delta = datetime.timedelta(seconds=60 * 15)
    if 'Expires' in req.params.keys():
        expr_time = _get_time(req.params['Expires'])
        if expr_time > nw + delta:
            log(logging.WARN, "The request for user %s has an expiration time that is too far in the future." % (access_id))
            raise PhantomAWSException('RequestExpired')
    if not expr_time and 'Timestamp' in req.params.keys():
        timestamp = _get_time(req.params['Timestamp'])
        if timestamp > nw + delta:
            log(logging.WARN, "The request for user %s has a timestamp that is too far in the future." % (access_id))
            raise PhantomAWSException('RequestExpired')
        expr_time = timestamp + delta
    if not expr_time:
        log(logging.WARN, "The request for user %s neither a timestamp nor expiration time." % (access_id))
        raise PhantomAWSException('MissingParameter')
    if nw > expr_time:
        log(logging.WARN, "The request for user %s has no timestamp nor expiration time." % (access_id))
        raise PhantomAWSException('RequestExpired')


def calc_v2_signature(secret_key, req):
    string_to_sign = '%s\n%s\n%s\n' % (req.method, req.headers['host'].lower(), req.path)

    if req.params['SignatureMethod'] == 'HmacSHA256':
        l_hmac = hmac.new(secret_key, digestmod=sha256)
    else:
        l_hmac = hmac.new(secret_key, digestmod=sha1)

    keys = req.params.keys()
    keys.sort()
    pairs = []
    for key in keys:
        if key == 'Signature':
            continue
        val = boto.utils.get_utf8_value(req.params[key])
        pairs.append(urllib.quote(key, safe='') + '=' +
                     urllib.quote(val, safe='-_~'))
    qs = '&'.join(pairs)
    string_to_sign += qs
    l_hmac.update(string_to_sign)
    signature = base64.b64encode(l_hmac.digest())
    return signature

def calc_v1_signature(secret_key, req):
    return "X"

def calc_v0_signature(secret_key, req):
    return "Y"

def make_arn(name, requestId, type):
    arn = "arn:phantom:autoscaling:AZ:000000000000:launchConfiguration:%s:%s/%s" % (requestId, name, type)
    return arn
