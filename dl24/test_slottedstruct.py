import unittest

from slottedstruct import serializable_slotted_struct
from json_serializer import Serializer

Struct = serializable_slotted_struct('Struct', 'x', 'y')

class SlottedStructTestCase(unittest.TestCase):
    def test_serializes(self):
        o = Struct(x='a', y='b')
        s = Serializer.dumps(o)
        self.assertEqual(s, '{"_type": "Struct", "x": "a", "y": "b"}')
