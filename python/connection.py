#!/usr/bin/env python
# -*- coding: utf-8 -*-
from colors import bad, warn, info, good
import scanf
import sys

# args
def args(need=0, usage="usage: %s [args]" % sys.argv[0]):
	if len(sys.argv) < need+1:
		print usage
		sys.exit(1)
	else:
		return sys.argv[1:]
	

# tcp
class connection(object):
	def __init__(self, host='localhost', port=20003):
		'''connect to server'''
		import socket
		s = socket.socket()
		s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		s.connect((host,port))
		self.f = s.makefile('rw', 1)
		s.close()
#		self.f = file("pipe.3.read", 'r')
#		self.w = file("pipe.3.write", 'w')
	
	def __getattr__(self, name):
		'''cmd_STH forward to cmd(), else forward to self.f'''
		if name.startswith("cmd_"):
			def clo(*args, **kwargs):
				args = [name[4:].upper()] + list(args)
				return self.cmd(*args, **kwargs)
			return clo 
		else:
			return getattr(self.f, name)
				
	def _catch_read(self, fun):
		try: return fun(self)
		except EOFError:
			raise Exception(warn("połączenie zerwane"))			
	def readint(self):   return self._catch_read(scanf.readint)
	def readfloat(self): return self._catch_read(scanf.readfloat)
	def readstr(self):   return self._catch_read(scanf.readstr)
	def readline(self):  return self._catch_read(scanf.readline)
	
	
	def _read_ack(self):
		'''waits for OK'''
		result = self._readstr_assert(['OK', 'FAILED'])
		if result == 'FAILED':
			errno = self.readint()
			rest = self.readline()
			res = "FAILED " + str(errno) + " " + rest	
			print bad(res)
			if errno == 7: # next command will force waiting
				print bad(self.readline())
				self._read_ack()
			return res
		else:
			return ""
			
					
		
	def _readstr_assert(self, what):
		'''read token and make sure is in list what or equals string what'''
		result = self.readstr()
		if not isinstance(what, list):
			what = [what]
		if result not in what: print warn(result)
		return result
	
	def writeln(self, line):
		self.write(line+'\n')
	
	
	
	def login(self, name="team13", password="efemztzlxt"):
		'''login to server'''
		self._readstr_assert('LOGIN')
		self.writeln(name)
		self._readstr_assert('PASS')
		self.cmd(password)
	
	def cmd(self, what):
		'''sends command what, waits for OK, reads some lines'''
		self.writeln(what)
		res = self._read_ack()
		if res.startswith("FAILED 6"): # command limit reached
			return self.cmd(what)
		elif res.startswith("FAILED 7"): # force waiting
			return self.cmd(what)
		return res
	
	def wait(self):
		'''waits for next turn'''
		self.cmd_wait()
		print info(self.readline())
		self._read_ack()
	
	
	
	def score(self):
		self.cmd_get_score()
		return self.readfloat()
	
	def order_count(self):
		self.cmd_get_order_count()
		return self.readint()
	
	def time_to_cut(self):
		self.cmd_time_to_cut()
		return self.readint()
	
		
		
		
		
		
		




	
	
	
	
	
	

