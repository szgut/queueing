WARNINGS=-Wall -Wextra
LIBS=`sdl-config --libs` -lSDL_net -lm
CFLAGS=`sdl-config --cflags`

VERB=$(if $(VERBOSE),-DVERBOSE)

# default 'debug'
%: %.cpp debug.h dclient.hpp
	g++ $< -o $@ -g -ansi -O2 $(WARNINGS) $(CFLAGS) $(LIBS) $(VERB) -DDEBUG  

# 'release'
%.r: %.cpp debug.h dclient.hpp
	g++ $< -o $@ -g -ansi -O2 $(WARNINGS) $(CFLAGS) $(LIBS) $(VERB)
