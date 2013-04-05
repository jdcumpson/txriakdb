'''
Created on 2013-04-03

@author: Noobie
'''
from urllib import urlencode, quote
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


class Decoder(simplejson.JSONDecoder):
    pass

encoder = Encoder()
decoder = Decoder()

def solrencode(d):
    s = ' +'.join([':'.join((key, value)) for key,value in d.items()])
    return s


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
        props = {"precommit":[{"mod":"riak_search_kv_hook","fun":"precommit"}]}
        d = self.client.set_bucket_properties(cls.__riakmeta__.name,
                                              properties=props,
                                              )
        return d
        
    def get(self, cls, key):
        d = self.client.fetch_object(cls.__riakmeta__.name, key)
        d.addCallback(lambda json: cls(decoder.decode(json)))
        return d
    
    def find(self, cls, query, params=None):
        d = self.client.riak_search(cls.__riakmeta__.name, query=query)
        d.addCallback(decoder.decode)
        return d
    
    def find_by_index(self, cls, index, value):
        if len(index.split('_')) == 1:
            index += '_bin'
        d = self.client.si_search(cls.__riakmeta__.name, index, value)
        d.addCallback(decoder.decode)
        d.addCallback(lambda res:res['keys'])
        return d
    
    def find_one(self, cls, query, **kwargs):
        d = self.client.riak_search(cls.__riakmeta__.name, query=query,
                                    params={'rows':1})
        d.addCallback(decoder.decode)
        d.addCallback(lambda objs: objs[0])
        return d
    
    def find_one_by_index(self, cls, index):
        d = self.client.si_search(cls.__riakmeta__.name, index, value)
        d.addCallback(decoder.decode)
        return d
    
    def store(self, instance):
        headers = {}
        headers.update(self.client.headers)
        
        for i in instance.__class__.__riakmeta__.indexes:
            t = 'bin'
            if len(i) > 1:
                t = [1]
            index = '%s_%s' % (i[0], t)
            headers['x-riak-index-%s' % (index,)] = getattr(instance, i[0])
        d = self.client.store_object(instance.__class__.__riakmeta__.name,
                                     instance._id,
                                     instance,
                                     headers=headers,
                                     )
        return d
    
    def count(self, cls, index, value):
        d = self.client.si_search(cls.__riakmeta__.name, index, value)
        d.addCallback(decoder.decode)
        d.addCallback(lambda values:len(values))
        pass
    
    def delete(self, instance):
        d = self.client.delete_object(instance.__class__.__riakmeta__.name,
                                      instance._id,
                                      )
        return d
    
    def set(self, instance, **kwargs):
        pass
    
    def drop_indexes(self, cls):
        props = {"precommit":[]}
        d = self.client.set_bucket_properties(cls.__riakmeta__.name,
                                              properties=props,
                                              )
        return d
    
    def index_info(self, cls):
        raise NotImplementedError
    
    def riak_search(self, cls, *args, **kwargs):
        return self.client.riak_search(cls.__riakmeta__.name,
                                *args, **kwargs)
    
    def index_search(self, cls, *args, **kwargs):
        return self.client.si_search(client.__riakmeta__.name,
                                     *args, **kwargs)
    
    def mapred(self, cls, *args, **kwargs):
        return self.client.mapred(client.__riakmeta__.name,
                                  *args, **kwargs)
    


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
        # lame
        query = params.pop('q', None)
        p = urlencode(params)
            
        if len(p) > 0:
            if query:
                p += '&' + '='.join(('q', query))
            s = '?' + str(p)
        elif query:
            p += '='.join(('q', query))
             
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
        
    def store_object(self, bucket, key, object, params=None, headers=None):
        if not params:
            params = {'returnbody':'true'}
        url = self._make_url('/%s/keys/%s' % (bucket, key,), params=params)
        return self._get_url(url, postdata=encoder.encode(object),
                             method='PUT', headers=headers)
    
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
        return self._get_url(url, postdata=data, method="PUT")
    
    def reset_bucket_properties(self, bucket):
        url = self._make_url('/%s/props')
        return self._get_url(url, method='DELETE')
    
    def riak_search(self, bucket, query=None, params=None, *args, **kwargs):
        if not params:
            params = {}
        q = params.pop('query', None)
        if not query:
            query = q
            
        if not query:
            raise Exception('Invalid query! No query parameter.')
        
        query = solrencode(query)
        params['q'] = query
        params['wt'] = 'json'
        
        url = self._make_url('/solr/%s/select' % (bucket,), 
                             params,
                             no_prefix=True,
                             )
        
        # riak blows monkey nuts, so we have to use content-type: text/xml
        return self._get_url(url)
    
    def si_search(self, bucket, index, value, *args, **kwargs):
        """
        Perform a 2i search on the riak data.
        """
        url = self._make_url('/%s/index/%s/%s' % (bucket, index, value,))
        return self._get_url(url)
    
    def link_walk(self, bucket, *args, **kwargs):
        raise NotImplementedError
    
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
        raise NotImplementedError
    
    
