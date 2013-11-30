# -*- coding: utf-8 -*-
import socket
import time

from dl24 import log
from dl24 import misc
from dl24 import scanf


class CommandFailedError(Exception):
	def __new__(cls, msg, errno=None):
		exceptions = {6: ForcedWaitingError, 9: NoCurrentWorld}
		return super(CommandFailedError, cls).__new__(exceptions.get(errno, cls))
	def __init__(self, msg, errno=None):
		super(CommandFailedError, self).__init__(msg)
		self.errno = errno


class ForcedWaitingError(CommandFailedError):
	pass


class NoCurrentWorld(CommandFailedError):
	pass


class ConnectionResetError(Exception):
	pass


class Connection(object):
		
	def __init__(self, host='localhost', port=20003):
		self._host = host
		self._port = port
		self._connect_and_login()

	def _catch_read(self, fun):
		try: return fun(self.f)
		except EOFError:
			log.warn("połączenie zerwane")
			self._connect_and_login()
			raise ConnectionResetError
	
	def readint(self):   return self._catch_read(scanf.readint)
	def readfloat(self): return self._catch_read(scanf.readfloat)
	def readstr(self):   return self._catch_read(scanf.readstr)
	def readline(self):  return self._catch_read(scanf.readline)
	def readints(self, n):
		return list(map(lambda _: self.readint(), range(n)))
	
	def _read_ack(self):
		'''waits for OK'''
		OK, FAILED = 'OK', 'ERROR'
		result = self._readstr_assert([OK, FAILED])
		if result == FAILED:
			errno = self.readint()
			msg = self.readline()
			description = "FAILED " + str(errno) + " " + msg
			log.bad(description)
			if errno == 7: # forced waiting
				log.bad(self.readline()) # FORCED_WAITING secs
				self._read_ack()
			elif errno == 9:
				time.sleep(1)
			raise CommandFailedError(description, errno)

	def _readstr_assert(self, what):
		'''read token and make sure is in list what or equals string what'''
		result = self.readstr()
		if not isinstance(what, list):
			what = [what]
		if result not in what:
			log.warn(result)
		return result

	def writeln(self, *what):
		self.f.write(" ".join(map(str, misc.flatten(what))) +"\n")
	
	def _connect(self):
		'''connect to server'''
		s = socket.socket()
		s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		s.connect((self._host, self._port))
		self.f = s.makefile('r+', 1)
		s.close()
	
	@misc.insist((EOFError, socket.error), wait=2)
	def _connect_and_login(self):
		self._connect()
		self._login()

	def _login(self, name="team08", password="pqe8g44u4x"):
		'''login to server'''
		self._readstr_assert('LOGIN')
		self.writeln(name)
		self._readstr_assert('PASSWORD')
		self.cmd(password)

	def cmd(self, *what):
		'''sends command what, waits for OK, reads some lines'''
		while 1:
			self.writeln(*what)
			try:
				return self._read_ack()
			except (ForcedWaitingError, NoCurrentWorld, ConnectionResetError):
				pass	# repeat the command

	def throwing_cmd(self, *what):
		''' throws ForcedWaitingError '''
		while 1:
			self.writeln(*what)
			try:
				self._read_ack()
			except ConnectionResetError:
				pass	# repeat the command

	def wait(self):
		'''waits for next turn'''
		self.cmd('WAIT')
		log.info(self.readline())
		self._read_ack()
