import pygame


class Command(object):
	"""Command from client, created directly from json."""
	
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
		elif self.action == 'clear':
			thingsset.clear()
		elif self.action == 'set_title':
			pygame.display.set_caption(self.title)


class Thing(object):
	"""Set of points that knows how to draw itself."""
	
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

	@staticmethod
	def _scale(point, scale, _shift):
		(x, y), (sx, sy) = point, _shift
		return (x * scale - sx, y * scale - sy)

	@staticmethod
	def _square(point, width):
		return pygame.Rect(point, (width, width))

	def draw(self, screen, scale, _shift):
		for point in self.points:
			scaled_point = self._scale(point, scale, _shift)
			if scale == 1:
				pygame.draw.line(screen, self.color, scaled_point, scaled_point)
			else:
				pygame.draw.rect(screen, self.color, self._square(scaled_point, scale))

	def draw_label(self, screen, scale, _shift, font):
		label = font.render(self.label, 1, (255, 255, 0))
		screen.blit(label, self._scale(self.center, scale, _shift))


class ThingsSet(object):
	"""Set of displayed things."""

	def __init__(self):
		self.clear()

	def add(self, tid, thing):
		self._things[tid] = thing

	def remove(self, tid):
		try:
			del self._things[tid]
		except KeyError:
			pass

	def clear(self):
		self._things = {}

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
