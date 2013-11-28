from dl24.misc import sortedset

class Thing(object):
	def __init__(self, points, label='', color=(0,0,255)):
		self.points = map(tuple, points)
		self.label = label
		self.color = color
		self.center = self._mass_center()
	
	def _mass_center(self):
		if not self.points: return (0,0)
		cx, cy = 0.0, 0.0
		for x, y in self.points:
			cx += x
			cy += y
		return (cx/len(self.points), cy/len(self.points))
	
	def __repr__(self):
		return repr(self.points)


class Command(object):
	def __init__(self, action='add', tid=0, points=None, label='', color=(0,255,0), **kwargs):
		self.thing = Thing(points or [], label, color)
		self.action = action
		self.tid = tid
	
	def __call__(self, thingsset):
		if self.action == 'add':
			thingsset.add(self.tid, self.thing)
		elif self.action == 'remove':
			thingsset.remove(self.tid)


class ThingsSet(object):
	def __init__(self):
		self._things = {}
		self._heap_x = sortedset([0], getmax=True)
		self._heap_y = sortedset([0], getmax=True)
	
	def add(self, tid, thing):
		if tid in self._things:
			self._remove_old_points(self._things[tid])
		self._things[tid] = thing
		for x, y in thing.points:
			self._heap_x.add(x)
			self._heap_y.add(y)
	
	def remove(self, tid):
		self._remove_old_points(self._things[tid])
		del self._things[tid]
	
	def _remove_old_points(self, thing):
		for x, y in thing.points:
			self._heap_x.remove(x)
			self._heap_y.remove(y)		
	
	def reverse(self, point):
		return (point[0], self._heap_y.top() - point[1])
	
	def tids_at(self, point):
		for tid, thing in self._things.iteritems():
			if point in thing.points:
				yield tid
	
	def points(self, thing):
		for point in thing.points:
			yield self.reverse(point)
	
	@property
	def size(self):
		return self._heap_x.top(), self._heap_y.top()
	
	def __iter__(self):
		return self._things.itervalues()
	
	def __repr__(self):
		return repr(self._things)