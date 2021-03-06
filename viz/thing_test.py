import unittest

import thing

class TestThingsSet(unittest.TestCase):
	
	def test_size(self):
		ts = thing.ThingsSet()
		self.assertEqual(ts.size, (0,0))
		
		ts.add(1, thing.Thing([(1,2), (3, 0)])) 
		self.assertEqual(ts.size, (3,2))
		
		ts.add(4, thing.Thing([(7, 1)]))
		self.assertEqual(ts.size, (7,2))
		
		ts.remove(1)
		self.assertEqual(ts.size, (7,1))
		
		ts.add(4, thing.Thing([(5,4)]))
		self.assertEqual(ts.size, (5,4))


class TestAutotid(unittest.TestCase):

	def test_compare(self):
		a1, a2 = thing.Autotid(), thing.Autotid()
		self.assertTrue(a1 < a2)
		self.assertTrue(a1 < 1)
		self.assertTrue(a1 < -1)
		self.assertTrue(a1 < (0, 0))
