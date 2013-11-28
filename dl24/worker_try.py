import pickle
import socket

s = socket.socket()
s.connect(('localhost', 1234))
f = s.makefile('r+', 0)
s.close()

pi = pickle.Pickler(f, pickle.HIGHEST_PROTOCOL)
unpi = pickle.Unpickler(f)

while 1:
	obj = unpi.load()
	print obj
	pi.dump((obj, "lol"))