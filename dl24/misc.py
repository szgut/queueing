# -*- coding: utf-8 -*-
import functools
import colors
import cPickle as pickle

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