import pygame.event
import thing


class StopGui(Exception):
	"""Exception thrown to stop the GUI and exit main()."""
	pass


def schedule(callback):
	"""Executes callback in the event dispatch thread."""
	def post_custom_event(**kwargs):
		pygame.event.post(pygame.event.Event(pygame.USEREVENT, kwargs))
	post_custom_event(handle=callback)


class Gui(object):
	"""Base class that shows a window and handles _events."""

	def __init__(self, size):
		self._size = size

	def _set_screen_size(self, size):
		"""Resizes screen and redraws everything."""
		self._size = size
		self._screen = pygame.display.set_mode(self._size, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
		pygame.key.set_repeat(200, 35)
		self.render(self._screen)

	def loop(self):
		"""Displays screen and executes event loop."""
		self._set_screen_size(self._size)
		while True:
			pygame.event.pump()
			if any(map(self._handle_event, self._events())):
				self.render(self._screen)
			pygame.display.flip()

	@staticmethod
	def _events():
		"""Yields at least one event, more if available without waiting."""
		yield pygame.event.wait()
		for event in pygame.event.get():
			yield event

	def _handle_event(self, event):
		"""Calls event handler and returns whether the screen needs redrawing."""
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

	def handle_click(self, pos, button):
		pass

	def handle_keydown(self, key):
		pass

	def render(self, screen):
		pass


class Viz(Gui):
	"""Class that draws things on the screen."""

	# colors
	BLACK = (0, 0, 0)
	WHITE = (255, 255, 255)

	# mouse scrolling is translated to zooming with keyboard
	SCROLL_BTNS = {4: pygame.K_EQUALS, 5: pygame.K_MINUS}
	
	# mouse button for context label
	CONTEXT_BTN = 3

	ZOOM_STEP = 1.25
	# zooming with + and - keys
	ZOOM_KEYS = {pygame.K_EQUALS: ZOOM_STEP, pygame.K_MINUS: 1.0 / ZOOM_STEP}

	# moving the screen with cursors
	MOVE_KEYS = {pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0),
		 		 pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1)}


	def __init__(self, clicks_callback, *args):
		super(Viz, self).__init__(*args)
		self.clicks_callback = clicks_callback
		self._reset_zoom()
		self.things = thing.ThingsSet()
		self.context_label = None

	def _reset_zoom(self):
		"""Puts the screen back into initial position with no zoom."""
		self.O = (0, 0)  # shift in pixels before zooming 
		self.zoom = 1.0  # factor multiplicating width of square

	def handle_click(self, pos, button):
		if button == self.CONTEXT_BTN:
			if self.context_label is None:
				thing = self.things.topmost_thing(self._pos_to_point(pos))
				if thing is not None and thing.context_label:
					self.context_label = (pos, thing.context_label)
			else:
				self.context_label = None
		if button in self.SCROLL_BTNS:
			self._zoom(self.SCROLL_BTNS[button],
					   float(pos[0])/self._size[0], float(pos[1])/self._size[1])
		else:
			point = self._pos_to_point(pos)
			tids = list(self.things.tids_at(point))
			print point, tids
			self.clicks_callback(point, tids, button)
	
	def _pos_to_point(self, pos):
		"""Converts pixel coordinates to virtual point."""
		scale, shift = self._comp_scale(), self._shift()
		return ((pos[0] + shift[0])/scale, (pos[1]+shift[1])/scale)

	def handle_keydown(self, key):
		if key in self.MOVE_KEYS:
			p = self._comp_pxlen()
			v = self.MOVE_KEYS.get(key, (0, 0))
			self.O = (self.O[0] + p * v[0], self.O[1] + p * v[1])
		elif key in self.ZOOM_KEYS:
			self._zoom(key)
		if key == pygame.K_0:
			self._reset_zoom()

	def _zoom(self, key, kx=0.5, ky=0.5):
		"""Recomputes zoom and shift values after zooming."""
		z = self.ZOOM_KEYS[key]
		w, h = self._size
		x = self.O[0] + kx * (1 - 1.0 / z) * w / self.zoom
		y = self.O[1] + ky * (1 - 1.0 / z) * h / self.zoom
		self.O = (x, y)
		self.zoom *= z

	def _comp_pxlen(self):
		"""Returns length in pixels of one square, before zooming."""
		sqsz = self.things.size
		return max(1, min(self._size[0] / (sqsz[0] + 1), self._size[1] / (sqsz[1] + 1)))

	def _comp_scale(self):
		"""Returns length in pixels of one square, after zooming."""
		return int(round(self._comp_pxlen() * self.zoom))

	def _shift(self):
		"""Returns (x,y) shift in pixels applied to squares, after zooming."""
		return (int(self.O[0] * self.zoom), int(self.O[1] * self.zoom))

	def render(self, screen):
		pygame.draw.rect(screen, self.BLACK, pygame.Rect((0, 0), self._size))
		scale = self._comp_scale()
		shift = self._shift()
		font = pygame.font.SysFont("Sans", min(100, int(1.2*scale)))
		context_font = pygame.font.SysFont("Sans", 20)

		for thing in self.things:
			thing.draw(screen, scale, shift)

		for thing in self.things:
			thing.draw_label(screen, scale, shift, font)
		
		if self.context_label is not None:
			pos, text = self.context_label
			for i, line in enumerate(text.split('\n')):
				label = context_font.render(line, True, self.BLACK, self.WHITE)
				screen.blit(label, (pos[0], pos[1] + i * context_font.get_linesize()))


def main(clicks_callback=lambda x: None):
	"""Displays window, blocks until closed or ^C."""
	pygame.init()
	try:
		Viz(clicks_callback, (600, 600)).loop()
	except (KeyboardInterrupt, StopGui):
		pass
