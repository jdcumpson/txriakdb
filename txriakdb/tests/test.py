'''
Created on 2013-04-03

@author: Noobie
'''
import simplejson
from twisted.internet import defer

from txriakdb import client
from txriakdb import bucket
from txriakdb import schema
from txriakdb import objectid

riak_session = client.Session()
riak_client = client.Client(host='192.168.56.131', port=8091)
riak_session.bind(riak_client)

class Token(schema.Item):
    pass

class Logins(bucket.Bucket):
    
    class __riakmeta__:
        session = riak_session
        name = 'logins'
        indexes = ['username', 'user_id']
        
    _id = bucket.Field(schema.ObjectID)
    username = bucket.Field(str, required=True)
    password = bucket.Field(str, required=True)
    user_id = bucket.Field(schema.ObjectID, required=True)
    
        
class Administrators(bucket.Bucket):
    class __riakmeta__:
        session = riak_session
        name = 'administrators'
        indexes = ['username']
        
    _id = bucket.Field(schema.ObjectID) 
    verified = bucket.Field(bool, required=True)
    name = bucket.Field(str, required=True)
    email = bucket.Field(str)

def run():
    import sys
    from twisted.python import log
    log.startLogging(sys.stdout)
    defer.setDebugging(1)
    
    username = 'pi5'
    
    pi = Administrators({
                         '_id':objectid.ObjectId(),
                         'name':username, 
                         'email':'cumpsonjd@gmail.com',
                         'verified':True,
                         })
    
    pi_login = Logins({
                       '_id':objectid.ObjectId(),
                       'username':'pi',
                       'password':'raspberry',
                       'user_id':pi._id
                       })
    print pi
    print pi_login 
#    d = Logins.m.find({'username':'pi'})
    
    d = riak_client.list_keys('administrators')
    def delete_all(json):
        data = simplejson.loads(json)
        keys = data['keys']
        dl = []
        for key in keys:
            dl.append(riak_client.delete_object('administrators', key))
        return defer.gatherResults(dl)
            
    d.addCallback(delete_all)
    d.addErrback(log.err)
    d.addCallback(lambda _:riak_client.ping())
    d.addCallback(lambda res:log.msg('XXXX ping: %r' % (res,)))
    d.addErrback(log.err)
    d.addCallback(lambda _:riak_client.list_resources())
    d.addCallback(lambda res:log.msg('XXXX list resources: %r' % (res,)))
    d.addErrback(log.err)
    d.addCallback(lambda _:riak_client.status())
    d.addCallback(lambda res:log.msg('XXXX status: %r' % (res,)))
    d.addErrback(log.err)
    d.addCallback(lambda _:riak_client.list_buckets())
    d.addCallback(lambda res:log.msg('XXXX list buckets:%r' % (res,)))
    d.addErrback(log.err)
    d.addCallback(lambda _:riak_client.list_keys('administrators'))
    d.addCallback(lambda res:log.msg('XXXXX list users:%r' % (res,)))
    d.addErrback(log.err)
    d.addCallback(lambda _:riak_client.store_object('administrators', username, pi))
    d.addCallback(lambda res:log.msg('XXXXX store: %r' % (res)))
    d.addErrback(log.err)
    d.addCallback(lambda _ :riak_client.fetch_object('administrators', username))
    d.addCallback(lambda res:log.msg('XXXXX fetch: %r' % (res)))
    d.addErrback(log.err)
    d.addCallback(lambda _:riak_client.get_bucket_properties('administrators'))
    d.addCallback(lambda res:log.msg('XXXXX get_bucket_properties: %r' % (res)))
    d.addErrback(log.err)
    
    d.addCallback(lambda _:riak_client.set_bucket_properties('administrators',
                                                    {'last_write_wins':True}))
    d.addCallback(lambda res:log.msg('XXXXX-TRUE set_bucket_properties: %r' % (res)))
    d.addErrback(log.err)
    d.addCallback(lambda _:riak_client.set_bucket_properties('administrators',
                                                    {'last_write_wins':False}))
    d.addCallback(lambda res:log.msg('XXXXX-FALSE set_bucket_properties: %r' % (res)))
    d.addErrback(log.err)
    d.addCallback(lambda _:riak_client.delete_object('administrators', username))
    d.addCallback(lambda res:log.msg('XXXXX delete: %r' % (res)))
    d.addErrback(log.err)
    
    def list_keys():
        d.addCallback(lambda _:riak_client.list_keys('administrators'))
        d.addCallback(lambda res:log.msg('XXXXX list users:%r' % (res,)))
        
    from twisted.internet import reactor
    reactor.callLater(5, list_keys)
    reactor.run()

if __name__ == "__main__":
    run()