# -*- coding: utf-8 -*-
try:
	import cPickle as pickle
except ImportError:
	import pickle
import functools
import signal
import contextlib
import time
import heapq
import log

def insist(exception=KeyboardInterrupt, wait=None):
	def decorator(fun):
		@functools.wraps(fun)
		def wrapper(*args, **kwargs):
			while 1:
				try:
					return fun(*args, **kwargs)
				except exception:
					log.bad("retrying %s..." % fun.__name__)
					if wait is not None:
						time.sleep(wait)
		return wrapper
	return decorator


def flatten(*items):
	for item in items:
		if isinstance(item, str):
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
			log.info("wczytuję...")
			return pickle.load(f)

	def save(self, obj, suf=""):
		log.info("zapisuję...")
		with open(self.path+suf, 'wb') as f:
			pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)


@contextlib.contextmanager
def delay_sigint():
	exc = [False]
	def handler(signal, frame):
		exc[0] = True
	signal.signal(signal.SIGINT, handler)
	yield
	signal.signal(signal.SIGINT, signal.default_int_handler)
	if exc[0]:
		signal.default_int_handler()


class sortedset(object):
	def __init__(self, items=None, keyfun=None, getmax=False):
		self._keyfun = keyfun = keyfun or (lambda x: x)
		if getmax:
			self._keyfun = lambda x: -keyfun(x)
		self._heap = []
		self._correct_kvals = {}
		if items is not None:
			self.add_all(items)

	def add(self, item, key=None):
		kval = key if key is not None else self._keyfun(item)
		heapq.heappush(self._heap, (kval, item))
		self._correct_kvals[item] = kval

	def remove(self, item):
		del self._correct_kvals[item]

	def add_all(self, items):
		for item in items:
			self.add(item)

	keychanged = add

	def top(self):
		while self._heap:
			kval, item = self._heap[0]
			if kval == self._correct_kvals.get(item, (item,)):
				return item
			else:
				heapq.heappop(self._heap)
		raise IndexError("pop from empty sortedset")

	def pop(self):
		item = self.top()
		del self._correct_kvals[item]
		heapq.heappop(self._heap)
		return item


	def __contains__(self, item):
		return item in self._correct_kvals

	def __repr__(self):
		key = lambda item: self._correct_kvals[item]
		return "sortedset(%s)" % repr(sorted(self._correct_kvals, key=key))