from PIL import Image

class Png(object):
	def __init__(self, filename):
		self.filename = filename
		im = Image.open(filename)
		self.rgb = im.convert('RGB')
		self.w, self.h = self.rgb.size

	def __getitem__(self, xy):
		return self.rgb.getpixel(xy)

	def get_pixels(self):
		p = {}
		for x in range(0, self.w):
			for y in range(0, self.h):
				p[x, y] = self[x, y]
		return p
