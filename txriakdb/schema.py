"""
@todo: add schema enabled db.
"""

from datetime import datetime

class Item(object):
    
    def __init__(self, *args, **kwargs):
        """
        @todo: this should be invalid and should be per type of subclass
        """
        pass
    
    def validate(self, d):
        raise NotImplementedError
    
    @classmethod
    def make(cls, field, *args, **kwargs):
        """Build a SchemaItem from a "shorthand" schema (summarized below)

        int - int or long
        str - string or unicode
        float - float, int, or long
        bool - boolean value
        datetime - datetime.datetime object
        None - Anything
        
        [] - Array of Anything objects
        [type] - array of objects of type "type"
        { fld: type... } - dict-like object with fields of type "type"
        """
        if isinstance(field, list):
            if len(field) == 0:
                field = Array(Anything())
            elif len(field) == 1:
                field = Array(field[0])
            else:
                raise ValueError, 'Array must have 0-1 elements'
        elif isinstance(field, dict):
            field = Object(field)
        elif field is None:
            field = Anything()
        elif field in SHORTHAND:
            field = SHORTHAND[field]
        if isinstance(field, type):
            field = field(*args, **kwargs)
        if not isinstance(field, Item):
            field = Value(field)
        return field

class Value(Item):
    pass

class ObjectID(Item):
    pass

class Object(Item):
    pass

class Anything(Item):
    pass

class String(Item):
    pass

class Boolean(Item):
    pass

class Float(Item):
    pass

class Int(Item):
    pass

class Date(Item):
    pass


SHORTHAND = {
    int:Int,
    str:String,
    bool:Boolean,
    any:Anything,
    datetime:Date,
    float:Float,
}



