# -*- coding: utf-8 -*-
import functools
import colors
import cPickle as pickle
import sys

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


class Serializator(object):
	def __init__(self, path):
		self.path = path

	def load(self):
		with open(self.path, 'rb') as f:
			print colors.info("wczytuję...")
			return pickle.load(f)

	def save(self, obj):
		print colors.info("zapisuję...")
		with open(self.path, 'wb') as f:
			pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)


# argparse!
def args(need=0, usage="usage: %s [args]" % sys.argv[0]):
	if len(sys.argv) < need+1:
		print usage
		sys.exit(1)
	else:
		return sys.argv[1:]

def getparam(args, param):
    for arg in args:
        if arg.startswith(param):
            return int(arg.split('=')[1])
    return None

if __name__ == '__main__':
	from time import sleep

	count = 0

	@insist()
	def inc(limit):
		global count
		count += 1
		sleep(2)
		return count
		
	sys.stdout.write("%d\n" % inc(7000000))
