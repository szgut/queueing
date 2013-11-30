import time

import pygame.event
import thing


class StopGui(Exception):
	pass


def post_custom_event(**kwargs):
	pygame.event.post(pygame.event.Event(pygame.USEREVENT, kwargs))


def schedule(callback):
	post_custom_event(handle=callback)


class Gui(object):
	
	def __init__(self, size):
		self._size = size
		
	def _set_screen_size(self, size):
		self._size = size
		self._screen = pygame.display.set_mode(self._size, pygame.HWSURFACE|pygame.DOUBLEBUF|pygame.RESIZABLE)
		self.render(self._screen)
		
	def loop(self):
		self._set_screen_size(self._size)
		while True:
			pygame.event.pump()
			events = list(pygame.event.get())
			if events:
				for event in events:
					self._handle_event(event)
				self.render(self._screen)
				pygame.display.flip()
			else:
				time.sleep(0.1)
			

	def _handle_event(self, event):
		if event.type == pygame.QUIT:
			raise StopGui
		if event.type == pygame.VIDEORESIZE:
			self._set_screen_size(event.size)
		elif event.type == pygame.MOUSEBUTTONUP:
			self.handle_click(event.pos, event.button)
		elif event.type == pygame.USEREVENT:
			event.handle(self)

class Viz(Gui):
	shapes = [
		[], # 
		[((0,3),(6,3))], # 1
		[((0,3),(6,3)), ((3,0),(3,2)), ((3,4),(3,6))], # 2
		[((3,0),(3,1)), ((3,1),(1,3)), ((1,3),(0,3))], # 3
		[((3,0),(3,1)), ((3,1),(1,3)), ((1,3),(0,3)),
		 ((3,6),(3,5)), ((3,5),(5,3)), ((5,3),(6,3))], # 4
		[((0,3),(6,3)), ((3,0),(3,3))], # 5
		[((0,3),(6,3)), ((3,0),(3,6))], # 6
		[((0,3),(3,3))], # 6
	]
	
	@staticmethod
	def rotPoint(pkt, count, pxlen):
		x, y = pkt
		x -= 3
		y -= 3
		for _ in xrange(0, count):
			x, y = -y, x
		x += 3
		y += 3
		x *= pxlen
		x /= 6
		y *= pxlen
		y /= 6
		return (x, y)
		
	
	def __init__(self, callback, *args):
		super(Viz, self).__init__(*args)
		self.callback = callback
		
		self.things = thing.ThingsSet()
		#self.things.add(1, thing.Thing([(0,0), (2,0)], label=u"cos"))
		#self.things.add(2, thing.Thing([(1,1), (0,0)], color=(255,0,0), label="trzy"))
			
	def handle_click(self, pos, button):
		pxlen = self.comp_pxlen()
		rpoint = self.things.reverse((pos[0]/pxlen, pos[1]/pxlen))
		tids = list(self.things.tids_at(rpoint))
		print rpoint, tids
		self.callback(rpoint, tids, button)	
	
	@staticmethod
	def square(point, pxlen):
		x, y = point
		p1 = (x*pxlen, y*pxlen)
		return pygame.Rect(p1, (pxlen, pxlen))
	
	def comp_pxlen(self):
		sqsz = self.things.size
		return min(self._size[0]/(sqsz[0]+1), self._size[1]/(sqsz[1]+1))
	
	def center(self, point, pxlen):
		rpoint = self.things.reverse(point)
		return tuple(map(lambda x: (x+0.5)*pxlen, rpoint))
	
	def render(self, screen):
		pygame.draw.rect(screen, (0,0,0), pygame.Rect((0,0), self._size))
		myfont = pygame.font.SysFont("Sans", 15)
	
		pxlen = self.comp_pxlen()
		for _, thing in sorted(self.things.iteritems()):
			for point in self.things.points(thing):

				if thing.typ == None:
					pygame.draw.rect(screen, thing.color, self.square(point, pxlen))
				else:
					(orx, ory) = point
					(orx, ory) = (orx * pxlen, ory * pxlen)
					for (p1, p2) in self.shapes[thing.typ]:
						(p1x, p1y) = self.rotPoint(p1, thing.rot, pxlen)
						(p2x, p2y) = self.rotPoint(p2, thing.rot, pxlen)
						p1 = (orx + p1x, ory + p1y)
						p2 = (orx + p2x, ory + p2y)
						pygame.draw.line(screen, thing.color, p1, p2)
					if thing.typ >= 5:
						pos = (orx + pxlen/2, ory + pxlen/2)
						pygame.draw.circle(screen, thing.color, pos, 2)
				
		for thing in self.things:
			label = myfont.render(thing.label, 1, (255,255,0))
			screen.blit(label, self.center(thing.center, pxlen))		


def main(clicks_callback=lambda x: None):
	pygame.init()
	try:
		Viz(clicks_callback, (320, 240)).loop()
	except (KeyboardInterrupt, StopGui):
		pass
