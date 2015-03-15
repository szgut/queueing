#!/usr/bin/env python2
"""Module that handles connections with clients."""
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
	"""Opens socket on port and yields Connection instances, starts them."""
	sock = socket.socket()
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind(('localhost', port))
	sock.listen(1)
	while True:
		process = Connection(sock.accept()[0])
		yield process
		process.start()


def daemon_run(target):
	"""Runs callable target in deamon thread."""
	thread = threading.Thread(target=target)
	thread.daemon = True
	thread.start()


class Connection(multiprocessing.Process):
	"""Class that represents connection with client.
	Runnable in separate process."""

	def __init__(self, sock):
		super(Connection, self).__init__()
		self.sock = sock

	def run(self):
		sys.stdin.close()
		self.cfile = self.sock.makefile('r+', 1)

		pygame.init()
		daemon_run(self._read_socket_lines)
		gui.main(self._clicked_callback)
		self.sock.shutdown(socket.SHUT_WR)
		print 'closed gui', pygame.display.get_caption()[0]

	def _read_socket_lines(self):
		"""Reacts on user input. Run in separate thread."""
		sys.stdin.close()
		for line in self._socket_lines():
			try:
				self._handle_input(json.loads(line))
			except ValueError as e:
				print e
		print 'connection lost'
		gui.schedule(lambda *x: sys.exit())

	def _socket_lines(self):
		"""Yields lines from socket until closed."""
		try:
			while True:
				line = self.cfile.readline()
				if not line: break
				yield line
		except IOError:
			print 'closed'

	@staticmethod
	def _handle_input(obj):
		"""Executes json-parsed command."""
		if not isinstance(obj, dict):
			return
		cmd = thing.Command(**obj)
		while True:
			try:
				return gui.schedule(lambda gui: cmd(gui.things))
			except pygame.error:
				time.sleep(0)


	def _clicked_callback(self, point, tids, button):
		"""Callback invoked on click."""
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
