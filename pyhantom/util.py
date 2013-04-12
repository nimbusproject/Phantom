import time

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
import re
import webob.exc
import datetime
from pyhantom.phantom_exceptions import PhantomAWSException, PhantomNotImplementedException


def statsd(func):
    def call(phantom_service, *args, **kwargs):
        before = time.time()
        ret = func(phantom_service, *args, **kwargs)
        after = time.time()
        if phantom_service._cfg.statsd_client is not None:
            try:
                phantom_service._cfg.statsd_client.timing('autoscale.%s.timing' % str(phantom_service.__class__.__name__), (after - before) * 1000)
                phantom_service._cfg.statsd_client.incr('autoscale.%s.count' % str(phantom_service.__class__.__name__))
            except:
                logger = logging.getLogger("phantom")
                logger.exception("Failed to submit metrics")
        return ret
    return call

def log(lvl, message, printstack=False):
    logger = logging.getLogger("phantom")
    logger.log(lvl, message)

    if printstack:
        str = traceback.format_exc()
        logger.log(lvl, str)

def log_request(req, user_obj):
    log(logging.INFO, "Received request %s from user %s" % (str(req.params), user_obj.access_id))

def log_reply(doc, user_obj):
    log(logging.INFO, "Sending reply %s to user %s" % (doc.documentElement.toprettyxml(), user_obj.access_id))


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
        def wrapped(wsgiapp, req, *args, **kw):
            try:
                #user_obj = wsgiapp.get_user_obj(req)
                return func(wsgiapp, req, *args, **kw)
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

def get_and_normalize_header(req, key):
    val = req.headers[key].strip()
    if key.lower() == "host":
        ndx = val.find(":")
        if ndx > 0:
            val = val[0:ndx]
    return val

def calc_aws4_signature(secret_key, req, access_dict):

    cr = [req.method.upper(),]
    cr.append(req.path)
    cr.append(req.query_string)
    headers_to_sign_list = access_dict['SignedHeaders'].split(";")

    l = ['%s:%s' % (n.lower().strip(),
          get_and_normalize_header(req, n)) for n in headers_to_sign_list]
    l = sorted(l)
    cr.append('\n'.join(l) + '\n')
    cr.append(access_dict['SignedHeaders'])

    # For POST requests, boto encodes the parameters in the body using urllib.quote, turning spaces into %20.
    # However, our web framework reencodes the body and turns all %20 into +.
    # Restore the original body sent by boto using req.params (which contains decoded values with spaces).
    if req.method == "POST":
        keys = req.params.keys()
        keys.sort()
        pairs = []
        for key in keys:
            if key == 'Signature':
                continue
            val = boto.utils.get_utf8_value(req.params[key])
            pairs.append(urllib.quote(key, safe='') + '=' +
                         urllib.quote(val, safe='-_~'))
        body = '&'.join(pairs)
    else:
        body = req.body

    cr.append(sha256(body).hexdigest())

    canonical_request = '\n'.join(cr)

    sts_a = ['AWS4-HMAC-SHA256', req.headers['X-Amz-Date'], access_dict['CredentialScope'], sha256(canonical_request).hexdigest()]
    sts = '\n'.join(sts_a)

    return aws4_signature(req, sts, secret_key, access_dict)

def aws4_sign(key, msg, hex=False):
    if hex:
        sig = hmac.new(key, msg.encode('utf-8'), sha256).hexdigest()
    else:
        sig = hmac.new(key, msg.encode('utf-8'), sha256).digest()
    return sig


def aws4_signature(req, string_to_sign, key, access_dict):

    vals = access_dict['CredentialScope'].split('/')

    k_date = aws4_sign(('AWS4' + key).encode('utf-8'),
                          vals[0])
    k_region = aws4_sign(k_date, vals[1])
    k_service = aws4_sign(k_region, vals[2])
    k_signing = aws4_sign(k_service, vals[3])
    return aws4_sign(k_signing, string_to_sign, hex=True)


def get_auth_hash(secret_key, req, access_dict):
    if access_dict['SignatureVersion'] == '2':
        sig = calc_v2_signature(secret_key, req, access_dict)
    elif access_dict['SignatureVersion'] == '1':
        sig = calc_v1_signature(secret_key, req, access_dict)
    elif access_dict['SignatureVersion'] == '0':
        sig = calc_v0_signature(secret_key, req, access_dict)
    else:
        sig = calc_aws4_signature(secret_key, req, access_dict)
    return sig

def _get_time(str_time):
    str_time = str_time.replace("Z", "UTC")
    # in case the seconds are over provisioned
    str_time = re.sub('\..*', "UTC", str_time)
    return datetime.datetime.strptime(str_time, '%Y-%m-%dT%H:%M:%S%Z')

def make_time(datetimeobj):
    fmt = '%Y-%m-%dT%H:%M:%S.%fZ'
    dt = datetime.datetime.strftime(datetimeobj, fmt);
    return dt

def authenticate_user(secret_key, req, access_dict):
    access_id = access_dict['AWSAccessKeyId']
    signature = access_dict['Signature']

    if not secret_key:
        log(logging.WARN, "The user %s was not found." % (access_id))
        raise PhantomAWSException('InvalidClientTokenId')
    proper_signature = get_auth_hash(secret_key, req, access_dict)

    if signature != proper_signature:
        log(logging.WARN, "The signature for user %s was not correct." % (access_id))
        raise PhantomAWSException('IncompleteSignature')

    # check the time
    expr_time = None
    nw = datetime.datetime.utcnow()
    delta = datetime.timedelta(seconds=60 * 15)
    if 'Expires' in access_dict.keys():
        expr_time = _get_time(access_dict['Expires'])
        if expr_time > nw + delta:
            log(logging.WARN, "The request for user %s has an expiration time that is too far in the future." % (access_id))
            raise PhantomAWSException('RequestExpired')
    if not expr_time and 'Timestamp' in access_dict.keys():
        timestamp = _get_time(access_dict['Timestamp'])
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


def calc_v2_signature(secret_key, req, access_dict):
    string_to_sign = '%s\n%s\n%s\n' % (req.method, req.headers['host'].lower(), req.path)

    if access_dict['SignatureMethod'] == 'HmacSHA256':
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

def calc_v1_signature(secret_key, req, access_dict):
    return "X"

def calc_v0_signature(secret_key, req, access_dict):
    return "Y"

def make_arn(name, requestId, type):
    arn = "arn:phantom:autoscaling:AZ:000000000000:launchConfiguration:%s:%s/%s" % (requestId, name, type)
    return arn


def _get_aws_access_key_method_one(req):
    signature = req.params['Signature']
    key = req.params['AWSAccessKeyId']
    signature_method = req.params['SignatureMethod']

    res = {'AWSAccessKeyId': key, 'Signature': signature, 'SignatureMethod': signature_method, 'SignatureVersion': req.params['SignatureVersion']}

    optional_keys = ['Expires', 'Timestamp']
    for k in optional_keys:
        if k in req.params.keys():
            res[k] = req.params[k]

    return res

def _get_aws_access_key_method_two(req):
    auth_string_a = req.headers['Authorization'].split()
    metha = auth_string_a[0].split('-', 1)
    signature_method = metha[0]

    tokens = auth_string_a[1].split(',')

    res = {'Credential': None, 'Signature': None, 'SignedHeaders': None, 'SignatureMethod': signature_method, 'SignatureVersion': metha[1]}
    for t in tokens:
        for k in res.keys():
            ndx = t.find(k)
            if ndx == 0:
                res[k] = t[len(k) + 1:]

    found = False
    optional_keys = ['Expires', 'Timestamp']
    for k in optional_keys:
        if k in req.params.keys():
            res[k] = req.params[k]
            found = True
    if not found:
        dt_str =  req.headers['X-Amz-Date'].replace('Z', 'UTC')
        dt = datetime.datetime.strptime(dt_str, '%Y%m%dT%H%M%S%Z')
        dt_str2 = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        res['Timestamp'] = dt_str2

    for k in res.keys():
        if res[k] is None:
            PhantomAWSException("The key %s is required in the Authorization parameter.")

    a = res['Credential'].split('/', 1)
    res['AWSAccessKeyId'] = a[0]
    res['CredentialScope'] = a[1]

    return res


def get_aws_access_key(req):

    if 'AWSAccessKeyId' in req.params.keys():
        log(logging.INFO, "AWSAccessKeyId is in the request parameter list using authentication method one")
        return _get_aws_access_key_method_one(req)

    if 'Authorization' in req.headers.keys():
        log(logging.INFO, "Authorization is in the request parameter list using authentication method two")
        return _get_aws_access_key_method_two(req)

    raise PhantomAWSException('Unable to find the information needed to authenticate the user in the request')
