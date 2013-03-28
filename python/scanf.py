
def token(f):
	whitespace, l = ' \t\n', []
	while True:
		c = f.read(1)
		if not c:
			if len(l) and l[-1] not in whitespace: break
			else: raise EOFError
		elif c in whitespace and len(l) and l[-1] not in whitespace:
			break
		l.append(c)
	return ''.join(l)

def whole_line(f):
	l = []
	while True:
		c = f.read(1)
		if not c:
			if len(l): return ''.join(l)
			raise EOFError
		elif c=='\n':
			return ''.join(l)
		l.append(c)

def readint(f):	return int(token(f))
def readfloat(f): return float(token(f))
def readstr(f): return token(f).split()[0]
def readline(f):
	line = whole_line(f)
	return line if line.split() else readline(f)

if __name__ == '__main__':
	#from sys import stdin as inp
	import socket
	s = socket.socket()
	s.connect(('127.0.0.1', 1234))
	inp = s.makefile()
	
	n = readint(inp)
	l = []
	for i in range(0,n):
		l.append(token(inp))
	print l
	print map(int, l)
