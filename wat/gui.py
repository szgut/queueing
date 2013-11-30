from dl24.worker import *
import time
import threading

class Gui(threading.Thread):
	def __init__(self, universum, on_build = lambda: None):
		super(Gui, self).__init__()
		self.deamon = True
		self.w = Worker(title='universum %i' % universum)
		self.wcmd = Worker(title='universum %i - commands' % universum)
		time.sleep(0.5)
		self.update_command_window()
		self.on_build = on_build
		self.tool = 0
		self.rot = 0
		self.should_stop = False
		self.start()

	def update_command_window(self, conn = None):
		for t in range(1, 7):
			for rot in range(0, 4):
				if rot == 0:
					color = (100, 0, 0)
				elif rot == 1:
					color = (0, 100, 0)
				elif rot == 2:
					color = (100, 0, 100)
				elif rot == 3:
					color = (100, 100, 0)
				if rot == 0:
					if conn is not None:
						quant = str(conn.pipes[t])
					else:
						quant = "?"

					self.wcmd.command(tid=10*t + rot, label=quant,
							points=[(rot, t*2)],
							typ=t, rot=rot, color=color)
				else:
					self.wcmd.command(tid=10*t + rot, points=[(rot, t*2)],
							typ=t, rot=rot, color=color)

	def update_viz(self, m, conn):
		i = 0
		# pipes
		for rot in range(0, 4):
			for typ in range(1, 8):
				pts = []
				my_pts = []
				for (x, y), f in m.items():
					if f.t == typ and f.r == rot and f.water == 'N':
						if (f.team == conn.id):
							my_pts.append((x, y))
						else:
							pts.append((x, y))

				col = (50, 50, 50)
				colmy = (100, 100, 100)
				self.w.command(tid=i, points=pts, typ=typ, rot=rot, color=col)
				self.w.command(tid=i+1, points=my_pts, typ=typ, rot=rot, color=colmy)

				pts = []
				my_pts = []
				for (x, y), f in m.items():
					if f.t == typ and f.r == rot and f.water == 'W':
						if (f.team == conn.id):
							my_pts.append((x, y))
						else:
							pts.append((x, y))
				col = (20, 20, 100)
				colmy = (100, 100, 255)
				self.w.command(tid=i+2, points=pts, typ=typ, rot=rot, color=col)
				self.w.command(tid=i+3, points=my_pts, typ=typ, rot=rot, color=colmy)
				i += 4
		rocks = [(x, y) for ((x, y), f) in m.items() if f.kind == 'R']
		self.w.command(tid=i, points=rocks, color=(100, 100, 100))

		i = 0
		col = (255, 0, 255)
		for (x, y), cid in conn.my_contracts.items():
			col = (0, 255, 0)
			self.w.command(tid=-1000000+i, points=[(x, y)], color=col)
			i += 1

		col = (255, 0, 0)
		for (x, y), rot in conn.sources.items():
			self.w.command(tid=-1000000+i, points=[(x, y)], typ=7, rot=rot, color=col)
			i += 1

		self.update_command_window(conn)

	def get_clicks(self):
		clicks = []
		for elem in self.w.iterget():
			clicks.append((elem.point.x, elem.point.y, elem.button))
		return clicks

	def get_tool(self):
		ret = None
		for t in self.wcmd.iterget():
			if len(t.tidlist) == 0:
				continue
			ret = t.tidlist[0]/10, t.tidlist[0] % 10
		return ret

	def run(self):
		while not self.should_stop:
			ret = self.get_tool()
			if ret is not None:
				self.tool, self.rot = ret

			clicks = self.get_clicks()
			for (x, y, button) in clicks:
				self.on_build(x, y, button, self.tool, self.rot)

			time.sleep(0.05)

	def stop(self):
		self.should_stop = True
