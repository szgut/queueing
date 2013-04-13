from dl24.connection import Connection
from dl24.misc import Serializator
from dl24.colors import warn, bad, good, info


c = Connection() # connects to localhost:20003
c.cmd_dupa(3, [4, 5])