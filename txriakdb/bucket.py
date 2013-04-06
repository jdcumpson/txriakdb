'''
Created on 2013-04-03

@author: Noobie


This module allows you to run commands based on the riak-recommended operation
documentation.

@todo: Implement BSON for optimization of JSON.

@see: http://docs.basho.com/riak/1.2.1/tutorials/querying/Riak-Search/ 
@see: http://docs.basho.com/riak/1.2.1/tutorials/querying/Secondary-Indexes/
@see: http://docs.basho.com/riak/1.2.1/tutorials/querying/MapReduce/
@see: http://docs.basho.com/riak/latest/tutorials/querying/
'''

from txriakdb import client

class Field(object):

    def __init__(self, field_type, *args, **kwargs):
        self.type = field_type
        self.args = args
        self.kwargs = kwargs
        self.name = None

    def __get__(self, instance, cls):
        try:
            return instance[self.name]
        except KeyError:
            raise AttributeError, self.name

    def __set__(self, instance, value):
        instance[self.name] = value

    def __delete__(self, instance):
        del instance[self.name]


class BucketMeta(type):
    """@todo: implement schema enabled design"""
    def __init__(cls, name, bases, dct):
        pass

class ManagerDescriptor(object):
    def __init__(self, mgr_cls):
        self.mgr_cls = mgr_cls

    def __get__(self, instance, cls):
        return self.mgr_cls(instance, cls)


class Manager(object):
    
    def __init__(self, instance, cls):
        self.session = cls.__riakmeta__.session
        self.instance = instance
        self.cls = cls
        if self.session is not None:
            self.ensure_indexes()

    def __call__(self, session):
        '''In order to use an alternate session, just use Class.mgr(other_session)'''
        result = Manager(self.instance, self.cls)
        result.session = session
        return result
    
    def ensure_indexes(self):
        self.session.ensure_indexes(self.cls)
        
    def get(self, key):
        return self.session.get(self.cls, key)
    
    def all(self):
        return self.session.all(self.cls)
    
    def find(self, *args, **kwargs):
        """ Find a value in our bucket based on query parameters passed into
            the solr-like interface.
        """
        return self.session.find(self.cls, *args, **kwargs)
    
    def find_by_index(self, index, value):
        return self.session.find_by_index(self.cls, index, value)
    
    def find_one(self, *args, **kwargs):
        return self.session.find_one(self.cls, **kwargs)
    
    def find_one_by_index(self, index, value):
        return self.session.find_one_by_index(self.cls, index, value)
    
    def store(self):
        return self.session.store(self.instance)
    
    def count(self):
        return self.session.count(self.cls)
    
    def delete(self):
        return self.session.delete(self.instance)
    
    def set(self, **kwargs):
        return self.session.set(self.instance, **kwargs)
    
    def drop_indexes(self):
        return self.session.drop_indexes(self.cls)
    
    def index_info(self):
        return self.session.index_info(self.cls)
    
    #--- these are for custom functionality
    
    def riak_search(self, *args, **kwargs):
        return self.session.riak_search(self.cls, *args, **kwargs)
    
    def si_search(self, *args, **kwargs):
        return self.session.index_search(self.cls, *args, **kwargs)
   
    def mapred(self, *args, **kwargs):
        return self.session.mapred(self.cls, *args, **kwargs)


class DictLike(dict):
    'Dict providing object-like attr access'
    __slots__ = ()

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError, name

    def __setattr__(self, name, value):
        if name in self.__dict__:
            super(DictLike, self).__setattr__(name, value)
        else:
            self.__setitem__(name, value)


class Bucket(DictLike):
    """
    
    """
    __metaclass__ = BucketMeta
    _registry = {}
    m = ManagerDescriptor(Manager)
    
    class __riakmeta__:
        '''Supply various information on how the class is mapped without
        polluting the class's namespace.  In particular,

        @cvar name: collection name
        @cvar session: Session object managing the object (link to a DataStore)
        @cvar indexes: list of field name tuples specifying which indexes should exist
                  for the document
        '''
        name = None
        session = None
        indexes = []
        
    def __init__(self, data):
        if isinstance(data, str):
            data = simplejson.loads(data)
        elif not isinstance(data, dict):
            raise "Unknown object type, cannot load into bucket."
        dict.update(self, data)
        
    @classmethod
    def make(cls, data):
        return cls(data)

