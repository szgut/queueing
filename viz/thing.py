import pygame

class Thing(object):
	def __init__(self, points, label='', color=(0,0,255), **kwargs):
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
	def __init__(self, action='add', tid=0, points=None, label='', color=(0,255,0), title='', **kwargs):
		self.thing = Thing(points or [], label, color, **kwargs)
		self.action = action
		self.title = title
		if isinstance(tid, list):
			tid = tuple(tid)
		self.tid = tid
	
	def __call__(self, thingsset):
		if self.action == 'add':
			thingsset.add(self.tid, self.thing)
		elif self.action == 'remove':
			thingsset.remove(self.tid)
		elif self.action == 'set_title':
			pygame.display.set_caption(self.title)


class ThingsSet(object):
	def __init__(self):
		self._things = {}
	
	def add(self, tid, thing):
		self._things[tid] = thing
	
	def remove(self, tid):
		try:
			del self._things[tid]
		except KeyError:
			pass
	
	def reverse(self, point):
		return (point[0], self.size[1] - point[1])
	
	def tids_at(self, point):
		for tid, thing in self._things.iteritems():
			if point in thing.points:
				yield tid
	
	def points(self, thing):
		for point in thing.points:
			yield self.reverse(point)
	
	@property
	def size(self):
		maxx, maxy = 0, 0
		for thing in self:
			for point in thing.points:
				maxx = max(maxx, point[0])
				maxy = max(maxy, point[1])
		return (maxx, maxy)
	
	def __iter__(self):
		return self._things.itervalues()
	
	def __repr__(self):
		return repr(self._things)
	
	def iteritems(self):
		return self._things.iteritems()
