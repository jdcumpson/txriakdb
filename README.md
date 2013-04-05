txriakdb
========

A twisted plugin for using Riak databases with schema-enabled support.

This package provides a way to interface with Riak DB in a sane way that utilizes a cleaner and more precise method of loading, storing and querying data. The package provides a means to generate class definitions to explicitly define what data to expect from your NoSQL data store, using Riak's built in methods to accomplish the query.

Currently map reduce and link walking are NOT enabled, however they are being actively developed and are not far off - if any saavy contributors are feeling particularly enthused. See current implementation.

# What does this module provide?
- Simple, easy-to-use class style data definitions
- A querying interface that actually works (issues with txriak?)
- Easier way to use secondary indexes
- Easier way to use Riak with python
- Deferred-style loads

# 30-second (useful) demo
```
#!python

import sys
from twisted.internet import defer
from twisted.python import log
from txriakdb import bucket, client, schema, objectid

# log to standard out
log.startLogging(sys.stdout)

# make sure you change the database to your database info
riak_session = client.Session(client.Client(host='localhost',
                                            port=8091))
class Users(bucket.Bucket):
    class __riakmeta__:
        session = riak_session # give it an active 'session'
        name = 'users'         # name of the bucket in Riak
        indexes = [('email',)] # add email as property to be used as [secondary] index
                               # note: in this package index is the same as 2i
    _id = bucket.Field(schema.ObjectID)
    email = bucket.Field(str)
    password = bucket.Field(str)

def run():
    # make a new user, he's devilishly handsome
    jbond = Users({'_id':objectid.ObjectId(),
                  'email':'james@mi6.co.uk',
                  'password':'plaintextisbad'
                  })
    # store user in database (commit)
    d = jbond.store()
    # lookup a user by an index, let's try email index
    deferred = Users.m.find_by_index('email')
    deferred.addCallback(log.msg)
    # get a user by his _id
    d = Users.m.get(jbond._id) # _id would usually be from another value
    d.addCallback(log.msg)

if __name__ == "__main__":
    run()

```

# How can I contribute?
- Message me for information if you need, but adhering strictly to Riak docs, the mapred and linkwalk methods for clients need to be implemented, the framework is there and well defined.
- Testing and use-cases to clarify code
- Implementing schema validation (advanced)
