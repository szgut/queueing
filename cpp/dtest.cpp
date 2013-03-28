#include <cstdio>
#include <string>
#include "dclient.hpp"
#include "debug.h"
using namespace std;

int main() {
	DClient cl("127.0.0.1", 2222);
	cl.connect();
	while(true) {
		string s;
		int c = cl.getint();
		sockprintf(cl, "c=%d, 2*c=%d\n", c, c+c);
		
		cl.read_line(s);
		TIME; PV(s); N;
		cl.write(s + string(" MRYG\n"));
	}
	return 0;
}
