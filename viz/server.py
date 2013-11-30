#!/usr/bin/env python
import json
import multiprocessing
import socket
import sys
import threading

import pygame

import gui
import thing


def listen(port=1234):
	sock = socket.socket()
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind(('localhost', port))
	sock.listen(1)
	while True:
		process = Connection(sock.accept()[0])
		yield process
#		process.daemon = True
		process.start()
		


def daemon_run(target):
	thread = threading.Thread(target=target)
	thread.daemon = True
	thread.start()


class Connection(multiprocessing.Process):

	def __init__(self, sock):
		super(Connection, self).__init__()
		self.sock = sock

	def socket_lines(self):
		try:
			while True:
				line = self.cfile.readline()
				if not line: break
				yield line
		except IOError:
			print 'closed'
	
	def read_socket_lines(self):
		sys.stdin.close()
		for line in self.socket_lines():
			try:
				self.handle_input(json.loads(line))
			except ValueError as e:
				print e
		print 'connection lost'
		gui.schedule(lambda *x: sys.exit())

	def run(self):
		sys.stdin.close()
		self.cfile = self.sock.makefile('r+', 1)
		
		pygame.init()
		daemon_run(self.read_socket_lines)
		gui.main(self.clicked_callback)
		print 'gui closed'
	
	def handle_input(self, obj):
		if isinstance(obj, dict):
			gui.schedule(lambda gui: thing.Command(**obj)(gui.things))
	
	def clicked_callback(self, point, tids):
		try:
			print>>self.cfile, json.dumps((point, tids))
		except IOError as e:
			print e
	


def main():
	try:
		processes = []
		for process in listen():
			processes.append(process)
	except KeyboardInterrupt:
		print '\nkilling guis'
		for process in processes:
			process.terminate()

	
if __name__ == '__main__':
	main()