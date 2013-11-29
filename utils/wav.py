import wave
import struct

def bin_to_ints(samples):
	samples = [samples[i:i+4] for i in range(0, len(samples), 4)]
	return [struct.unpack_from("<i", samp)[0] for samp in samples]

def get_samples(filename, channels = 0):
	f = wave.open(filename, "rb")
	n = f.getnchannels()
	nf = f.getnframes()
	try:
		ret = []
		for ch in channels:
			if ch < n:
				ret.append(bin_to_ints(f.readframes(nf)))
			else:
				raise RuntimeError("channel not found: %i" % ch)
		return ret
	except TypeError:
		return bin_to_ints(f.readframes(nf))
