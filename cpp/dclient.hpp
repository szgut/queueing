#include <string>
#include "SDL.h"
#include "SDL_net.h"
#include "debug.h"
using namespace std;

char globalnystring[1000];
#define sockprintf(client, ...) sprintf(globalnystring, ##__VA_ARGS__), client.write(string(globalnystring))

class DClient
{
	private:
	string host;
	short port;
	IPaddress ip;
	TCPsocket sock;
	int send_bytes(const char*, int);
	int read_bytes(char*, int);

	public:
	DClient(const char*, short);
	~DClient();
	void connect();
	int write(const string&);
	int write_line(const string&);
	int read_line(string&);
	char getchar();
	int getint();
};

DClient::DClient(const char *_host, short _port)
{
	host = string(_host);
	port = _port;
	D(PN("Initializing SDLNet"));
	if(SDL_Init(0) == -1) {
		STAMP; PN(CRED CBRT "Problem in SDL_Init: " CRESET CRED "%s",
			SDL_GetError());
		exit(1);
	}
	if(SDLNet_Init() == -1) {
		STAMP; PN(CRED CBRT "Problem in SDLNet_Init: " CRESET CRED "%s",
			SDLNet_GetError());
		exit(1);
	}
	D(PN("Resolving %s...", _host));
	if(SDLNet_ResolveHost(&ip, _host, port) == -1) {
		STAMP; PN(CRED CBRT "Problem in SDLNet_ResolveHost: " CRESET CRED "%s",
			SDLNet_GetError());
		exit(2);
	}
	D(P("Host resolution: "); PV(ip.host); PV(ip.port); N);
}

DClient::~DClient()
{
	SDLNet_Quit();
	SDL_Quit();
}

void DClient::connect()
{
	sock = SDLNet_TCP_Open(&ip);
	if(!sock) {
		PN(CRED CBRT "Connection problem, SDLNet_TCP_Open: " CRESET CRED "%s",
			SDLNet_GetError());
		exit(3);
	}
	TIME; PN("Successfully connected to %s:%i", host.c_str(), port);
}

int DClient::send_bytes(const char* message, int len)
{
	int ret;
	ret = SDLNet_TCP_Send(sock, message, len);
	if(ret < len) {
		PN(CRED CBRT "Error sending text, SDLNet_TCP_Send: " CRESET CRED "%s",
			SDLNet_GetError());
		D(PN("Sent only %i bytes of %i, first 32 bytes of message:\n`%.32s'",
			ret, len, message));
		return -1;
	}
	return 0;
}

int DClient::read_bytes(char *buffer, int len)
{
	int ret;
	ret = SDLNet_TCP_Recv(sock, buffer, len);
	if(ret <= 0) {
		PN(CRED CBRT "Error reading text, SDLNet_TCP_Recv: " CRESET CRED "%s",
			SDLNet_GetError());
		return -1;
	}
	return 0;
}

int DClient::write(const string &message)
{
	int ret = send_bytes(message.c_str(), message.size());
	if(ret != 0)
		return ret;
#ifdef VERBOSE
	P(CGREEN CBRT "localhost>\n[begin]");
	P(CGREEN "%s", message.c_str());
	PN(CGREEN CBRT "[end]");
#endif
	return 0;
}

int DClient::write_line(const string &line)
{
	string message(line);
	message += '\n';
	int ret = send_bytes(message.c_str(), message.size());
	if(ret != 0)
		return ret;
#ifdef VERBOSE
	PN(CGREEN CBRT "localhost>" CRESET CGREEN " %s", line.c_str());
#endif
	return 0;
}

int DClient::read_line(string &message)
{
	int ret;
	char b;
	message = string("");
	do {
		ret = read_bytes(&b, 1);
		message += b;
	} while(ret == 0 && b != '\n');
	if(ret != 0)
		return -1;
	message.resize(message.size() - 1);
#ifdef VERBOSE
	PN(CGREEN CBRT "%s:%i>" CRESET CGREEN " %s",
		host.c_str(), port, message.c_str());
#endif
	return 0;
}

char DClient::getchar() {
	char c;
	read_bytes(&c, 1);
	return c;
}

int DClient::getint() {
	string s;
	char c;
	
	do {c = getchar(); s += c;}
	while(c<'0' || '9'<c);
	for(c=getchar(); '0'<=c && c<='9'; c=getchar()) s+=c;
	
	int i; sscanf(s.c_str(), "%d", &i);	
	return i;
}




