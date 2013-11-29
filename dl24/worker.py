import contextlib
import json
import Queue
import socket
import threading

from dl24 import scanf
from dl24 import slottedstruct
from dl24 import log


class Point(slottedstruct.SlottedStruct):
	__slots__ = ('x', 'y')


class Click(slottedstruct.SlottedStruct):
	__slots__ = ('point', 'tidlist')


class Worker(threading.Thread):

	def __init__(self, host='localhost', port=1234, autostart=True):
		super(Worker, self).__init__()
		self.daemon = True
		self._queue = Queue.Queue()
		self._connect(host, port)
		if autostart:
			self.start()

	def _connect(self, host, port):
		sock = socket.socket()
		sock.connect((host, port))
		with contextlib.closing(sock):
			self.cfile = sock.makefile('r+', 0)

	def handle_line(self, line):
		try:
			obj = json.loads(line)
			click = Click(Point(*obj[0]), obj[1])
		except (ValueError, IndexError) as e:
			log.warn(e)
		self._queue.put(click)

	def run(self):
		try:
			while True:
				line = self.cfile.readline()
				if not line: break
				self.handle_line(line)
		except IOError:
			log.warn('gui connection closed')

	def iterget(self):
		try:
			while True:
				yield self._queue.get_nowait()
		except Queue.Empty:
			pass

	def command(self, **kwargs):
		try:
			print>>self.cfile, json.dumps(kwargs)
			return True
		except (IOError, socket.error):
			return False


if __name__ == '__main__':
	w = Worker()
	w.command(tid=123, points=[(1,2), (2,3), (3,4)])
	try:
		while True:
			print w._queue.get()
	except KeyboardInterrupt:
		print "dupa"
	