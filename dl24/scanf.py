
def token(f):
	whitespace, l = ' \t\n', []
	while 1:
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
	while 1:
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
	while 1:
		line = whole_line(f)
		if line.split():
			return line