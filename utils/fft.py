import numpy

def amplitude(cmplx, N):
	return abs(cmplx)/N

def fft(samples):
	N = len(samples)
	fr = numpy.fft.fft(samples)
	return [amplitude(x, N) for x in fr]

# example:
#
# import wav
# samples = wav.get_samples("../t.wav", 0)
# f = fft(samples)
# for i, x in enumerate(f):
# 	print(i, x)
