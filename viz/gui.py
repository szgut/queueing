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
		self._screen = pygame.display.set_mode(self._size, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
		pygame.key.set_repeat(200, 35)
		self.render(self._screen)

	@staticmethod
	def events():
		yield pygame.event.wait()
		event = pygame.event.poll()
		while event.type != pygame.NOEVENT:
			yield event
			event = pygame.event.poll()

	def loop(self):
		self._set_screen_size(self._size)
		while True:
			pygame.event.pump()
			if any(map(self._handle_event, self.events())):
				self.render(self._screen)
			pygame.display.flip()

	def _handle_event(self, event):
		if event.type == pygame.QUIT:
			raise StopGui
		if event.type == pygame.VIDEORESIZE:
			self._set_screen_size(event.size)
		elif event.type == pygame.MOUSEBUTTONUP:
			self.handle_click(event.pos, event.button)
		elif event.type == pygame.KEYDOWN:
			self.handle_keydown(event.key)
		elif event.type == pygame.USEREVENT:
			event.handle(self)
		elif event.type == pygame.MOUSEMOTION:
			return False
		return True


class Viz(Gui):

	SCROLL_BTNS = {4: pygame.K_EQUALS, 5: pygame.K_MINUS}
	ZOOM_STEP = 1.25
	Z = {pygame.K_EQUALS: ZOOM_STEP, pygame.K_MINUS: 1 / ZOOM_STEP}
	V = {pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0),
		 pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1)}

	def __init__(self, callback, *args):
		super(Viz, self).__init__(*args)
		self.callback = callback
		self._reset_zoom()
		self.things = thing.ThingsSet()

	def _reset_zoom(self):
		self.O = (0, 0)
		self.zoom = 1.0

	def handle_click(self, pos, button):
		if button in self.SCROLL_BTNS:
			self._zoom(self.SCROLL_BTNS[button],
					   float(pos[0])/self._size[0], float(pos[1])/self._size[1])
		else:
			scale, shift = self.comp_scale(), self.shift()
			point = ((pos[0] + shift[0])/scale, (pos[1]+shift[1])/scale)
			tids = list(self.things.tids_at(point))
			print point, tids
			self.callback(point, tids, button)

	def handle_keydown(self, key):
		if key in self.V:
			p = self.comp_pxlen()
			v = self.V.get(key, (0, 0))
			self.O = (self.O[0] + p * v[0], self.O[1] + p * v[1])
		elif key in self.Z:
			self._zoom(key)
		if key == pygame.K_0:
			self._reset_zoom()

	def _zoom(self, key, kx=0.5, ky=0.5):
		z = self.Z[key]
		w, h = self._size
		x = self.O[0] + kx * (1 - 1.0 / z) * w / self.zoom
		y = self.O[1] + ky * (1 - 1.0 / z) * h / self.zoom
		self.O = (x, y)
		self.zoom *= z

	def comp_pxlen(self):
		sqsz = self.things.size
		return max(1, min(self._size[0] / (sqsz[0] + 1), self._size[1] / (sqsz[1] + 1)))

	def comp_scale(self):
		return int(round(self.comp_pxlen() * self.zoom))

	def shift(self):
		return (int(self.O[0] * self.zoom), int(self.O[1] * self.zoom))

	def render(self, screen):
		pygame.draw.rect(screen, (0, 0, 0), pygame.Rect((0, 0), self._size))
		scale = self.comp_scale()
		shift = self.shift()
		font = pygame.font.SysFont("Sans", min(100, int(1.2*scale)))

		for _, thing in sorted(self.things.iteritems()):
			thing.draw(screen, scale, shift)

		for thing in self.things:
			thing.draw_label(screen, scale, shift, font)


def main(clicks_callback=lambda x: None):
	pygame.init()
	try:
		Viz(clicks_callback, (600, 600)).loop()
	except (KeyboardInterrupt, StopGui):
		pass
