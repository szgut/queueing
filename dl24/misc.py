# -*- coding: utf-8 -*-
import functools
import signal
import contextlib
import cPickle as pickle
import colors

def insist(exception=KeyboardInterrupt):
	def decorator(fun):
		@functools.wraps(fun)
		def wrapper(*args, **kwargs):
			while 1:
				try:
					return fun(*args, **kwargs)
				except exception:
					print colors.bad("retrying %s...\n" % fun.__name__)
		return wrapper
	return decorator


def flatten(*items):
	for item in items:
		if isinstance(item, basestring):
			yield item
		else:
			try:
				for elem in flatten(*item):
					yield elem
			except TypeError:
				yield item


class Serializer(object):
	def __init__(self, path):
		self.path = path

	def load(self):
		with open(self.path, 'rb') as f:
			print colors.info("wczytuję...")
			return pickle.load(f)

	def save(self, obj, suf=""):
		print colors.info("zapisuję...")
		with open(self.path+suf, 'wb') as f:
			pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)


@contextlib.contextmanager
def delay_sigint():
	exc = [False]
	def handler(signal, frame):
		exc[0] = True
	signal.signal(signal.SIGINT, handler)
	yield
	signal.signal(signal.SIGINT, signal.SIG_DFL)
	if exc[0]:
		raise KeyboardInterrupt