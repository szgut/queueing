import json
from json import JSONEncoder

""" simple JSON serializer
    Usage:

    @serializable('a', 'x')
    class SomeClass(object):
        def __init__(self, a):
            self.a = a
            self.x = a + 10

        def inc(self):
            self.x += 1

        # this should construct SomeClass object using arguments passed to @serializable...
        # if this method is missing, the constructor is used instead (for simple objects)
        @staticmethod
        def construct(a, x):
            s = SomeClass(a)
            s.x = x
            return s

    s = SomeClass(3)
    s.inc() # s.a = 3, s.b = 14

    dump = Serializer.dumps(s)

    s.inc()
    s.inc() # s.a = 3, s.b = 16

    s = Serializer.loads(dump) # s.a = 3, s.b = 14

    Python does not serialize dicts correctly if keys are not strings
    (they are automatically converted to strings).
    In order to serialize dicts correctly use as_anydict wrapper:

    @serializable('x', as_anydict('y'), 'z')
    class ...

    Serializing to file:
    Serializer.dump(obj, file_name)
    ...
    obj = Serializer.load(filename)
"""

class serializable(object):
    def __init__(self, *attrs):
        self._attrs = attrs

    def __call__(self, cls):
        Serializer.register_class_attributes(cls, self._attrs)
        return cls

class Serializer(object):
    _registered_classes = {}
    @classmethod
    def register_class_attributes(cls, class_, attrs):
        if not isinstance(class_, type):
            raise TypeError("argument must be class")
        cname = class_.__name__
        if cname in cls._registered_classes:
            raise ValueError("class %s already serializable" % class_)
        cls._registered_classes[cname] = (class_, attrs)

    @classmethod
    def get_class_attributes(cls, cname):
        if isinstance(cname, type):
            cname = cname.__name__
        if cname not in cls._registered_classes:
            raise ValueError("class %s not serializable" % cname)
        return cls._registered_classes[cname]

    @staticmethod
    def wrapper_name(attr):
        if isinstance(attr, Wrapper):
            return attr.name
        else:
            return attr

    @staticmethod
    def wrap(obj, attr):
        if isinstance(attr, Wrapper):
            val = getattr(obj, attr.name)
            return attr.wrap(val)
        else:
            return getattr(obj, attr)

    class JSONSerializerEncoder(JSONEncoder):
        def default(self, obj):
            try:
                _, attrs = Serializer.get_class_attributes(type(obj))
                d = {Serializer.wrapper_name(attr): Serializer.wrap(obj, attr) for attr in attrs}
                d['_type'] = type(obj).__name__
                return d
            except ValueError:
                return super(Serializer.JSONSerializerEncoder, self).default(obj)

    @staticmethod
    def from_json(jo):
        try:
            t = jo['_type'] # KeyError
            cls, attrs = Serializer.get_class_attributes(t) # ValueError
        except (ValueError, KeyError):
            return jo
        attr_vals = {Serializer.wrapper_name(attr): jo[Serializer.wrapper_name(attr)] for attr in attrs}
        if hasattr(cls, 'construct'):
            return cls.construct(**attr_vals)
        else:
            return cls(**attr_vals)

    @classmethod
    def dumps(cls, obj):
        return json.dumps(obj, cls=cls.JSONSerializerEncoder, sort_keys=True)

    @classmethod
    def dump(cls, obj, fname):
        with open(fname, 'w') as fp:
            json.dump(obj, fp, cls=cls.JSONSerializerEncoder, sort_keys=True)

    @classmethod
    def loads(cls, s):
        return json.loads(s, object_hook=cls.from_json)

    @classmethod
    def load(cls, fname):
        with open(fname, 'r') as fp:
            return json.load(fp, object_hook=cls.from_json)

class Wrapper(object):
    def __init__(self, attr_name, tp):
        if not isinstance(attr_name, str):
            raise TypeError("Wrapper: argument attr_name must be string")
        if not callable(tp):
            raise TypeError("Wrapper: argument tp must be callable")
        self._attr_name = attr_name
        self._tp = tp

    @property
    def name(self):
        return self._attr_name

    def wrap(self, val):
        return self._tp(val)

@serializable('value')
class AnyDict(object):
    def __init__(self, d):
        self._d = d

    @property
    def value(self):
        return list(self._d.items())

    @staticmethod
    def construct(value):
        return dict(value)

def as_anydict(s):
    return Wrapper(s, AnyDict)
