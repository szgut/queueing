# -*- coding: utf-8 -*-
import socket
import log
import scanf
import misc
	
class CommandFailedError(Exception):
	def __new__(cls, msg, errno=None):
		exceptions = {6: ForcedWaitingError}
		return super(CommandFailedError, cls).__new__(exceptions.get(errno, cls))
	def __init__(self, msg, errno=None):
		super(CommandFailedError, self).__init__(msg)
		self.errno = errno
class ForcedWaitingError(CommandFailedError): pass

class ConnectionResetError(Exception): pass

# tcp
class Connection(object):
		
	def __init__(self, host='localhost', port=20003):
		self._host = host
		self._port = port
		self._connect_and_login()


	def __getattr__(self, name):
		'''cmd_STH forward to cmd() '''
		if name.startswith("cmd_"):
			def clo(*what):
				return self.cmd(name[4:].upper(), *what)
			return clo
		else:
			raise AttributeError(name)
	
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
		result = self._readstr_assert(['OK', 'FAILED'])
		if result == 'FAILED':
			errno = self.readint()
			msg = self.readline()
			description = "FAILED " + str(errno) + " " + msg
			log.bad(description)
			if errno == 6: # forced waiting
				log.bad(self.readline()) # FORCED_WAITING secs
				self._read_ack()
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
		self.write(" ".join(map(str, misc.flatten(what))) +"\n")

	
	def _connect(self):
		'''connect to server'''
		s = socket.socket()
		s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		s.connect((self._host, self._port))
		self.f = s.makefile('rw', 1)
		s.close()
	
	@misc.insist((EOFError, socket.error), 2)
	def _connect_and_login(self):
		self._connect()
		self._login()


	def _login(self, name="team9", password="emefbvvxle"):
		'''login to server'''
		self._readstr_assert('LOGIN')
		self.writeln(name)
		self._readstr_assert('PASS')
		self.cmd(password)
	

	def cmd(self, *what):
		'''sends command what, waits for OK, reads some lines'''
		while 1:
			self.writeln(*what)
			try:
				return self._read_ack()
			except (ForcedWaitingError, ConnectionResetError):
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
		self.cmd_wait()
		log.info(self.readline())
		self._read_ack()
