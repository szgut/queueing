import sys
import functools

def insist(exception=KeyboardInterrupt):
	def decorator(fun):
		@functools.wraps(fun)
		def wrapper(*args, **kwargs):
			while 1:
				try:
					return fun(*args, **kwargs)
				except exception:
					sys.stderr.write("retrying %s...\n" % fun.__name__)
		return wrapper
	return decorator
	

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
