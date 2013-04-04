'''
Created on 2013-04-03

@author: Noobie
'''
from urllib import urlencode
from datetime import datetime

import simplejson
from twisted.web.http_headers import Headers
from twisted.web import http
from twisted.web import client
from twisted.python import log

from txriakdb import objectid


class Encoder(simplejson.JSONEncoder):
    
    def default(self, o):
        if isinstance(o, datetime):
            return self.encode(dict(year=o.year, month=o.month, day=o.day, 
                                    hour=o.hour, minute=o.minute,second=o.second)) 
        if isinstance(o, objectid.ObjectId):
            return str(o)
        return super(Encoder,self).default(o)

encoder = Encoder()


class HTTPPageGetter(client.HTTPPageGetter):

    def handleEndHeaders(self):
        http.HTTPClient.handleEndHeaders(self)
    handleStatus_204 = lambda self: self.handleStatus_200()

class HTTPClientFactory(client.HTTPClientFactory):
    
    protocol = HTTPPageGetter
    
def getPage(url, contextFactory=None, *args, **kwargs):
    return client._makeGetterFactory(
            url,
            HTTPClientFactory,
            contextFactory=contextFactory, *args, **kwargs).deferred


class Session(object):
    """
    A proxy object tat we can call commands to the client object with.
    
    @attention: Normal usage does not need this, 'please BucketSubClass.m' 
                (Manager) to make database calls.
    
    @see: txriakdb.bucket.Bucket
    @see: txriakdb.bucket.Manager
    """
    
    client = None
    
    def bind(self, client):
        self.client = client
        
    def ensure_indexes(self, cls):
        pass
        
    def get(self, cls, key):
        pass
    
    def find(self, cls, *args, **kwargs):
        pass
    
    def find_by_index(self, cls, index):
        pass
    
    def find_one(self, cls, **kwargs):
        pass
    
    def find_one_by_index(self, cls, index):
        pass
    
    def save(self, instance):
        pass
    
    def count(self, cls):
        pass
    
    def delete(self, instance):
        pass
    
    def set(self, instance, **kwargs):
        pass
    
    def drop_indexes(self, cls):
        pass
    
    def index_info(self, cls):
        pass
    
    def riak_search(self, cls, *args, **kwargs):
        pass
    
    def index_search(self, cls, *args, **kwargs):
        pass
    
    def mapred(self, cls, *args, **kwargs):
        pass
    


class Client(object):
    """
    Normal usage should not need to call these methods. You should use the
    schema style implementation and use the BucketSubClass.m (manager) to do
    any commands.
     
    @see: http://docs.basho.com/riak/latest/references/apis/
    """
    
    def __init__(self, host, port, format='new', r=None, pr=None,
                 basic_quorum=None, secure=False, encoding='json'):
        """
        
        @param host: riak db host address
        @param port: riak db port
        @param format: use old or new style, defaults to new
        @param r: default r value for requests, not set by default
        @param pr: default pr value for requests, not set by default
        @param basic_quorum: default quorum for requests, not set by default
        @param secure: if True, use HTTPS (requires riak configured to https)
        @param encoding: what kind of object encoding, valid values are 'json',
                        'bson', 'binary'
                        
        @see: http://docs.basho.com/riak/latest/references/apis/
                for information about 'new' and 'old' formats, and api in
                general.
        """
        self.host = host
        self.port = port
        self.format = format
        self.r = r
        self.pr = pr
        self.quorum = basic_quorum
        self.secure = secure
        
        if encoding is not 'json':
            raise Exception('The encoding type \'%s\' is not supported yet.' % (encoding,))
        
        headers = {
            'Content-Type':'application/%s' % (encoding,),
            'Accept':'application/%s' % (encoding,)
        }
        self.headers = headers
        
    def _make_params(self, params, **kwargs):
        if params is not None and not isinstance(params, dict):
            raise Exception("Params not a dict instance, requires dict!")
        if not params:
            params = {}
            params.update(kwargs)
            
        s = ''
        p = urlencode(params)
        if len(p) > 0:
            s = '?' + str(p)
            
        return s
        
    def _make_url(self, append_to, params=None, no_prefix=False):
        secure = 's' if self.secure else ''
        prefix = '/buckets' if self.format == 'new' else '/riak'
        
        if no_prefix:
            prefix = ''
        
        url = 'http%s://%s:%s%s%s%s' % (secure, 
                                       self.host, 
                                       self.port, 
                                       prefix,
                                       append_to,
                                       self._make_params(params),
                                     )
        url = str(url)
        return url
    
    def _get_url(self, url, postdata=None, headers=None, method='GET'):
        if not headers:
            headers = self.headers
            
        log.msg('HEADERS: %s' %(headers,))
        d = getPage(url, method=method, postdata=postdata, headers=headers,
                    agent='txriakdb client')
        
        return d
        
    def fetch_object(self, bucket, key, params=None):
        """
        @param params: A dictionary with optional parameters:
                        'r': read quorum,
                        'pr': primary replicas,
                        'basic_quorum': return early logic,
                        'notfound_ok': whether notfounds are success or fail
                        'vtag': which sibling to retrieve
                        
        @see: http://docs.basho.com/riak/latest/references/apis/http/HTTP-Fetch-Object/
        """
        url = self._make_url('/%s/keys/%s' % (bucket, key,), params=params)
        return self._get_url(url)
        
    def store_object(self, bucket, key, data, params=None):
        if not params:
            params = {'returnbody':'true'}
        url = self._make_url('/%s/keys/%s' % (bucket, key,), params=params)
        return self._get_url(url, postdata=encoder.encode(data),
                             method='PUT')
    
    def delete_object(self, bucket, key, params=None):
        url = self._make_url('/%s/keys/%s' % (bucket, key,), params)
        return self._get_url(url, method='DELETE')

    #--- bucket methods
    def list_keys(self, bucket):
        url = self._make_url('/%s/keys' % (bucket), {'keys':'true'})
        return self._get_url(url)
    
    def get_bucket_properties(self, bucket):
        url = self._make_url('/%s/props' % (bucket,))
        return self._get_url(url)
    
    def set_bucket_properties(self, bucket, properties):
        url = self._make_url('/%s/props' %  (bucket,))
        data = encoder.encode({'props':properties})
        return self._get_url(url, postdata=data)
    
    def reset_bucket_properties(self, bucket):
        url = self._make_url('/%s/props')
        return self._get_url(url, method='DELETE')
    
    def riak_search(self, bucket, params, *args, **kwargs):
        pass
    
    def index_search(self, bucket, index, *args, **kwargs):
        pass
    
    def link_walk(self, bucket, *args, **kwargs):
        pass
    
    #--- database methods
    def list_buckets(self):
        url = self._make_url('', params={'buckets':'true'})
        return self._get_url(url)
    
    def ping(self):
        url = self._make_url('/ping', no_prefix=True)
        return self._get_url(url)
    
    def status(self):
        url = self._make_url('/stats', no_prefix=True)
        return self._get_url(url)
    
    def list_resources(self):
        url = self._make_url('/', no_prefix=True)
        return self._get_url(url)
    
    def mapred(self, bucket, function, params, *args, **kwargs):
        pass
    
    
