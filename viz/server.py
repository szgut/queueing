#!/usr/bin/env python
import json
import multiprocessing
import socket
import sys
import time
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

	@staticmethod
	def handle_input(obj):
		if not isinstance(obj, dict):
			return
		cmd = thing.Command(**obj)
		while True:
			try:
				return gui.schedule(lambda gui: cmd(gui.things))
			except pygame.error:
				time.sleep(0)

	def run(self):
		sys.stdin.close()
		self.cfile = self.sock.makefile('r+', 1)

		pygame.init()
		daemon_run(self.read_socket_lines)
		gui.main(self.clicked_callback)
		self.sock.shutdown(socket.SHUT_WR)
		print 'closed gui', pygame.display.get_caption()[0]

	def clicked_callback(self, point, tids, button):
		try:
			print>>self.cfile, json.dumps((point, tids, button))
		except IOError as e:
			print e


def main():
	try:
		processes = []
		for process in listen():
			processes.append(process)
	except:
		print '\nkilling guis'
		for process in processes:
			process.terminate()


if __name__ == '__main__':
	main()
