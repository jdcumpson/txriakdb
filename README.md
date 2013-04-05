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

# FAQ's

<b>Q: Riak is complaining about secondary indexes, what's the deal?</b>
A: You probably are trying to use indexing without the proper backend.
Riak requires that the eleveldb backend be enabled for secondary indexing
(2i) to work. Also regular 'find' queries must have the solr interface 
enabled in order to work. See your 'app.conf' in rel/riak/etc/. 

<b>Q: What are the parameters that I can use with queries for this database?</b>
A: 
-find(solr): http://docs.basho.com/riak/1.2.1/cookbooks/Riak-Search---Querying/#Querying-via-the-Solr-Interface
-find_by_index(2i): http://docs.basho.com/riak/1.2.1/tutorials/Secondary-Indexes---Examples/
-mapred: http://docs.basho.com/riak/1.2.1/tutorials/querying/MapReduce/

<b>Q: I don't know what I'm using riak for, are there any good examples?</b>
A:http://docs.basho.com/riak/1.2.1/cookbooks/use-cases/

<b>Q: Why would I use this package instead of riakdb?<b>
A: I was working on a distributed cloud system for a security-based project, and I found it
nearly impossible to use txriak. I think it stems from the riak library being 'too open'.
I stress 'too open' because everything feels like it's a hack. It feels like every time I
want to make a query it's a struggle. So I made txriak db in order to declutter the overall
experience with the database, as well as make it <i>very explicit</i> in what objects are
for and what they contain.

In short: compile (code) time explicitness vs. hand-crafted run-time queries


<b>Q: Is this module MIT?</b>
A: Yes completely open-sourced!

Copyright (c) 2013 JD Cumpson

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

