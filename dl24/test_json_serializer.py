import unittest

from json_serializer import Serializer, serializable, as_anydict

@serializable('a', 'b')
class A(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    @property
    def c(self):
        """ not serialized """
        return 10

    def __eq__(self, o):
        return self.a == o.a and self.b == o.b and self.c == o.c

@serializable('x', 'y')
class B(object):
    def __init__(self, x, y):
        self._x = x
        self._y = y

    @staticmethod
    def construct(x, y):
        return B(x, y - 10)

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y + 10

    def __eq__(self, o):
        return self.x == o.x and self.y == o.y

@serializable(as_anydict('d'))
class C(object):
    def __init__(self, d):
        self.d = d

    def __eq__(self, o):
        return self.d == o.d

class JSONSerializerTestCase(unittest.TestCase):
    def test_serializes_simple(self):
        a = A(2, 3)
        self.assertEqual(Serializer.dumps(a), '{"_type": "A", "a": 2, "b": 3}')

    def test_serializes_complex(self):
        b = B(A(2, 3), 15)
        self.assertEqual(Serializer.dumps(b), '{"_type": "B", "x": {"_type": "A", "a": 2, "b": 3}, "y": 25}')

    def test_deserializes_simple(self):
        o = Serializer.loads('{"_type": "B", "x": 1, "y": 2}')
        self.assertIsNotNone(o)
        self.assertEqual(o.x, 1)
        self.assertEqual(o.y, 2)

        o = Serializer.loads('{"_type": "A", "a": 1, "b": 2}')
        self.assertIsNotNone(o)
        self.assertEqual(o.a, 1)
        self.assertEqual(o.b, 2)

    def test_deserializes_complex(self):
        s = '{"_type": "B", "x": {"_type": "A", "a": 2, "b": 3}, "y": 25}'
        o = B(A(2, 3), 15)
        self.assertEqual(Serializer.loads(s), o)

    def test_serializes_deserializes(self):
        o = B(A(5, "123"), 14)
        s = Serializer.dumps(o)
        self.assertEqual(o, Serializer.loads(s))

    def test_serializes_deserializes_builtin_and_complex(self):
        c = C({1: A(2, B(C({1:4}), 4)), "c": "d"})
        s = Serializer.dumps(c)
        o = Serializer.loads(s)
        self.assertIsNotNone(o)
        self.assertDictEqual(o.d, c.d)
