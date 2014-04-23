CXX=g++ -std=c++0x -Wall -Wextra -Ofast -I $$HOME/kod/include

_blah.so: wdx.i wdx.cc wdx.h Makefile
	swig -builtin -Wall -c++ -debug-classes -python wdx.i
	$(CXX) -c -fpic wdx_wrap.cxx -I/usr/include/python2.7/
	$(CXX) -c -fpic wdx.cc -I../include/
	$(CXX) -shared wdx_wrap.o wdx.o -ljansson -o _wdx.so

clean:
	rm -f *.o *.so *wrap*
