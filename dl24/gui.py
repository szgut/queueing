# -*- coding: utf-8 -*-
import contextlib
import json
import socket
import threading

from dl24 import slottedstruct
from dl24 import log


class Color(object):
	BLACK = (0, 0, 0)
	WHITE = (255, 255, 255)
	GRAY = (30, 30, 30)

	RED = (255, 0, 0)
	GREEN = (0, 255, 0)
	BLUE = (0, 0, 255)

	LIGHT_BLUE = (100, 100, 255)
	YELLOW = (255, 255, 0)
	BROWN = (150, 60, 0)


class Button(object):
	LEFT = 1
	RIGHT = 3
	SCROLL_UP = 4
	SCROLL_DOWN = 5
	SCROLL_LEFT = 6
	SCROLL_RIGHT = 7


class Point(slottedstruct.SlottedStruct):
	__slots__ = ('x', 'y')


class Click(slottedstruct.SlottedStruct):
	__slots__ = ('point', 'tidlist', 'button')


class Clicker(object):
	def __call__(self, click):
		print click


class Worker(threading.Thread):

	def __init__(self, title=None, gui_hostport=('localhost', 1234),
				 autostart=True, clicker=Clicker()):
		super(Worker, self).__init__()
		self.daemon = True
		self._clicker = clicker
		self._cfile = self._connect_gui(gui_hostport)
		if title is not None:
			self.command(action='set_title', title=title)
		if autostart:
			self.start()

	def _connect_gui(self, hostport):
		sock = socket.socket()
		sock.connect(hostport)
		with contextlib.closing(sock):
			return sock.makefile('r+', 1)

	@staticmethod
	def _parse_click(line):
		try:
			obj = json.loads(line)
			return Click(Point(*obj[0]), obj[1], obj[2])
		except (ValueError, IndexError) as e:
			log.warn(e)

	def run(self):
		print "running"
		try:
			while True:
				line = self._cfile.readline()
				if not line: break
				self._clicker(self._parse_click(line))
		except IOError:
			log.warn('gui connection closed')

	def command(self, **kwargs):
		try:
			print >> self._cfile, json.dumps(kwargs)
			return True
		except (IOError, socket.error):
			return False


if __name__ == '__main__':
	w = Worker(title='Muminki')
	w.command(tid=(6, "bla"), points=[(1, 2), (2, 3), (3, 4)], label='siedę')
	for x in xrange(6):
		w.command(tid=x+10, points=[(x,x)], color=Color.LIGHT_BLUE)
	w.join()
