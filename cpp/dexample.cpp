#include "debug.h"

using namespace std;

int main(int argc, char **argv)
{
	/* Inform about periodic actions using a timestamp */
	TIME; PN("Starting the program");
	char* a = "asdkgha";
	int b = 123;
	/* Report variable values */
	PV(a); PV(b); N;
	/* In places where something that needs debugging may happen,
	 * print the stamp */
	STAMP; PN("Ooops, here is a problematic place, error code: " CRED "%i", b);
	/* Use notmal functions to write to stdout,
	 * you can still use colors */
	printf("This is a standard message " CBLUE "with some colors " CRESET CUND "and text attributes" CRESET ".\n");
	/* When something which should never happen happens... */
	FUCK(PN("This is really very bad. The computer will " CRED "explode"));
	TIME; PN("Exitting");
	return 0;
}
