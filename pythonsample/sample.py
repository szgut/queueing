import dl24.connection
import dl24.misc
from dl24.misc import getparam
from dl24.colors import warn, bad, good, info

class config(object):
	datafile = 'data'
	host = 'localhost'
	port = 1234


class Connection(dl24.connection.Connection):
	def __init__(self):
		super(Connection, self).__init__(config.host, config.port)

	# implementacja komend z zadania
	def dupa(self):
		self.cmd_dupa(3, [4, 5])
		return self.readints(2)


def init_state(read):
	global global_sth
	if read:
		global_sth = serializator.read()
	else:
		global_sth = 123


def loop():
	pass


if __name__ == '__main__':
	args = dl24.misc.args()
	#conn = Connection()
	serializator = dl24.misc.Serializator(config.datafile)

	print good(getparam(args, "pam"))

	init_state(False)
	try:
		while 1:
			loop()
	except KeyboardInterrupt:
		serializator.save(global_sth)