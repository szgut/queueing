import contextlib
import pickle
import Queue
import socket
import threading


class Worker(threading.Thread):

	def __init__(self, port, host='localhost', autostart=True):  # main thread
		super(Worker, self).__init__()
		self.daemon = True
		self.queue = Queue.Queue()
		self._server_socket = None
		self._pickler = None
		self._unpickler = None
		self._listen(host, port)
		if autostart:
			self.start()

	def _listen(self, host, port):  # main thread
		self._server_socket = s = socket.socket()
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind((host, port))
		s.listen(0)

	def _connect_client(self):  # worker thread
		client_socket, _addr = self._server_socket.accept()
		print _addr
		with contextlib.closing(client_socket.makefile('r+b', 0)) as _file:
			self._pickler = pickle.Pickler(_file, pickle.HIGHEST_PROTOCOL)
			self._unpickler = pickle.Unpickler(_file)

	def _handle_reads(self):  # worker thread
		while True:
			obj = self._unpickler.load()
			self.queue.put_nowait(obj)

	def run(self):  # worker thread
		while True:
			self._connect_client()
			try:
				self._handle_reads()
			except EOFError:
				pass

	def iterget(self):  # main thread
		while True:
			try:
				yield self.queue.get_nowait()
			except Queue.Empty:
				break

	def put(self, obj):  # main thread
		try:
			self._pickler.dump(obj)
			return True
		except (AttributeError, socket.error):
			return False


if __name__ == '__main__':
	import readline
	w = Worker(1234)
	while 1:
		obj = input('> ')
		if obj:
			print w.put(obj)
		else:
			print list(w.iterget())