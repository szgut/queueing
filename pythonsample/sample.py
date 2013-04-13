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

	def dupa(self):
		self.cmd_dupa(3, [4, 5])
		return self.readints(2)


serializator = dl24.misc.Serializator(config.datafile)
args = dl24.misc.args()
conn = Connection()

print good(getparam(args, "pam"))
try:
	print conn.dupa()
except dl24.connection.CommandFailedError as e:
	print e.errno