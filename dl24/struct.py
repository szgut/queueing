#!/usr/bin/env python2

class SlottedStruct(object):
	__slots__ = ()
	
	def __init__(self, *args, **kwargs):
		for name, arg in zip(self.__slots__, args) + kwargs.items():
			setattr(self, name, arg)

	def __getattr__(self, name):
		return None

	def __iter__(self):
		for name in self.__slots__:
			yield getattr(self, name)

	def __hash__(self):
		return hash(tuple(self))

	def __cmp__(self, other):
		state = lambda obj: [type(obj)]+list(obj)
		return cmp(state(self), state(other))

	def __repr__(self):
		get = lambda attr: attr + "=" + repr(getattr(self, attr))
		return "%s(%s)" % (type(self).__name__, ", ".join(map(get, self.__slots__)))


if __name__ == '__main__':

	class Ifka(SlottedStruct):
		__slots__ = 'x', 'y'
		def sum(self):
			return self.x + self.y

	class Lol(SlottedStruct):
		__slots__ = 'x', 'y'

	class Pam(SlottedStruct):
		pass

	print Pam()


	print (Ifka(y=4, x=5))
	print (Ifka(12, y="dupa"))
	print (list(Ifka(1)))
	print (str(Ifka()))

	a = Ifka(1,2)
	b = Ifka(2,3)
	c = Lol(1,2)
	print (a < b, b < a, a < c, c < a)
	print (map(hash,[a,b,c]))
	print (set([a,b,c]))
	print (sorted([a,b,c]))
	print (map(type, [a,b,c]))
	print (str(type(a)), repr(type(b)))