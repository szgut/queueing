#include <vector>

void put(int x, int y, int typ, int rot, bool wet);

void create(int xx, int yy);

struct Wybory {
	std::vector<std::pair< std::pair<int,int>, std::pair<int,int> > > v;
	int size() { return v.size(); }
	int x(int i) { return v[i].first.first; }
	int y(int i) { return v[i].first.second; }
	int typ(int i) { return v[i].second.first; }
	int rot(int i) { return v[i].second.second; }
};

Wybory ask(int x, int y);
