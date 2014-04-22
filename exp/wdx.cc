#include <krdln/includy.hpp>
#include <krdln/tcp.hpp>
#include <krdln/range.hpp>
#include "wdx.h"
#include <krdln/json.hpp>
using namespace krdln;

string ss2s(ostream const& os) {
	return dynamic_cast<stringstream const&>(os).str();
}

struct P {
	int x, y;
	
	P(int x, int y) : x(x), y(y) {}
	
	P(json_t * json) {
		vector<int> tmp = FromJson<vector<int>>()(json);
		x = tmp[0];
		y = tmp[1];
	}
	
	json_t * toJson() const {
		return ToJson<vector<int>>()({x,y});
	}
	
	bool operator < (P const& p) const {
		return tie(x,y) < tie(p.x, p.y);
	}
	
	P operator + (P const& p) const { return {x + p.x, y + p.y}; }
	P operator - (P const& p) const { return {x - p.x, y - p.y}; }
	
	bool operator == (P const& p) const { return x == p.x && y == p.y; }
	bool operator != (P const& p) const { return ! (*this == p); }
};

vector<P> DIRS = {{1,0},{-1,0},{0,1},{0,-1}};

struct Command {
	string action;
	vector<P> points;
	vector<int> color;
	string label;
	int tid;
	Command(
		vector<P> const& pts,
		vector<int> const& color,
		string label = "",
		int tid = 0
	) : action("add"), points(pts), color(color), label(label), tid(tid) {}
	Command(
		P p,
		vector<int> const& color,
		int tid = 0
	) : action("add"), points{p}, color(color), tid(tid) {}
	Command(char const * action, int tid = 0) : action(action), tid(tid) {}
	
	IMPLEMENT_JSON(Command,
		JSON_FIELD(action),
		JSON_FIELD(label),
		JSON_FIELD(tid),
		JSON_FIELD(color),
		JSON_FIELD(points)
	)
};

struct Viz : Socket {
	Viz() : Socket("127.0.0.1", "1234") {}
	
	void clear(int tid) {
		send({ {}, {0,0,0}, "", tid});
	}
	
	void send(Command const& c) {
		string cmd = toJsonStr(c) + "\n";
		// print cmd;
		assert(write(fd, cmd.c_str(), cmd.length())>=0);
	}
	vector<vector<int>> get() {
		char buf[1005];
		ssize_t len = read(fd, buf, 1000);
		buf[len] = 0;
		prerr buf;
		assert(len > 0);
		return {};
	}
};

// ---------------------------------------------------------------------

struct Mon { int attack; float value; };

struct Oth {
	P coo;
	int attack;
};

struct Expl {
	int id;
	P coo;
	int attack;
	float weapon;
	int monsters;
	float value;
	float capacity;
	int busy;
	Move move;
	bool assigned;
	
	float opt_cap() const {
		return capacity * 2 / 3;
	}
	
	int slowness() const {
		return value > opt_cap() ? 2 : 1;
	}
	
	Expl(int id, int x, int y, int a, float w, int m, float v, float c, int b) :
		id(id), coo{x,y}, attack(a), weapon(w), monsters(m), value(v), capacity(c), busy(b)
	{}
};

vector<string> maze;
map<P, float> treasures;
set<P> ass_tr;
map<P, Mon> monsters;
vector<Expl> mine;
set<P> mineset;
vector<Oth> others;
// vector<vector<P>> oldirs;
int WI, HE;
int ttcollapse;

const int TRESTART = 20000;
const int MONSTART = 30000;
const int MINSTART = 40000;
const int OTHSTART = 10000;

const int INF = 2123456789;

// initialization

Viz viz;

void set_ttc(int ttc) {
	ttcollapse = ttc;
}

void set_dims(int wi, int he) {
	WI = wi;
	HE = he;
	maze.clear();
	maze.push_back("");
}

void push_row(char const * str) {
	maze.push_back(string("#") + str);
	
	if ((int)maze.size() == HE + 1) {
		vector<P> walls;
		vector<P> exits;
		vector<P> armories;
		for (int r : inclusive(1, HE)) {
			for (int c : inclusive(1, WI)) {
				if (maze[r][c] == '#') walls.push_back({c,r});
				if (maze[r][c] == 'E') exits.push_back({c,r});
				if (maze[r][c] == 'A') armories.push_back({c,r});
			}
		}
		viz.send({walls, {130,120,100}, "", 1});
		viz.send({exits, {0,255,255}, "", 50000});
		viz.send({armories, {50,255,0}, "", 3});
	}
}

void clear_treasures() {
	int i = 0;
	for (auto const& p : treasures) {
		viz.clear(TRESTART + i++);
	}
	treasures.clear();
}

void add_treasure(int x, int y, float v) {
	treasures[{x,y}] = v;
	viz.send({
		{{x,y}},
		{200,100,0},
		ss2s(stringstream() << v),
		TRESTART + (int)treasures.size()}
	);
}

void clear_monsters() {
	int i = 0;
	for (auto const& p : monsters) {
		viz.clear(MONSTART + i++);
	}
	monsters.clear();
}

void add_monster(int x, int y, int a, float v) {
	monsters[{x,y}] = {a,v};
	viz.send({
		{{x,y}},
		{255,0,0},
		ss2s(stringstream() << a << "," << v),
		MONSTART + (int)monsters.size()
	});
}

void clear_others() {
	others.clear();
}
void add_other(int x, int y, int a) {
	others.push_back({{x,y},a});
}

void clear_mine() {
	mine.clear();
	mineset.clear();
}
void add_mine(
	int id, int x, int y, int attack, float weapon, int monsters,
	float value, float capacity, int busy
	) {
	mine.emplace_back(id, x, y, attack, weapon, monsters, value, capacity, busy);
	mineset.insert({x,y});
	// print attack;
}

void paint() {
	vector<P> v;
	for (Oth const& o : others) {
		v.push_back(o.coo);
	}
	viz.send({ v, {150,0,0}, "", 10});
	v.clear();
	
	for (Expl const& e : mine) {
		v.push_back(e.coo);
	}
	viz.send({ v, {255,0,255}, "", 11});
}


// -------------------------------------------------

template<class T>
auto at(T & v, P coo) -> decltype((v[0][0])) {
	return v[coo.y][coo.x];
}

void reset_flood(vector<vector<int>> & v) {
	v.assign(HE + 1, vector<int>(WI + 1, INF));
}

void do_flood(P start, vector<vector<int>> & v) {
	int odl = 0;
	queue<P> skm;
	at(v, start) = 0;
	skm.push(start);
	while (!skm.empty()) {
		++odl;
		queue<P> zkm;
		while (!skm.empty()) {
			P a = skm.front();
			// viz.send({ a, {255,255,255}, 42});
			// viz.get();
			skm.pop();
			for (P dir : DIRS) {
				P b = a + dir;
				if (at(maze, b) != '#')
				if (monsters.count(b) == 0)
				if (odl < at(v, b)) {
					at(v, b) = odl;
					zkm.push(b);
				}
			}
		}
		skm = move(zkm);
	}
}

P first_step(P start, P end, int odl, vector<vector<int>> & flood) {
	for (P dir : DIRS) {
		P here = end + dir;
		if (at(flood, here) != odl - 1) continue;
		if (here == start) return end;
		P ret = first_step(start, here, odl - 1, flood);
		if (ret == P{0,0}) continue;
		return ret;
	}
	return {0,0};
}

void ufajnij(vector<vector<float>> & f, P start, float power, float step, float znak) {
	set<P> used;
	queue<P> skm;
	skm.push(start);
	used.insert(start);
	while (!skm.empty() && power > 0) {
		queue<P> zkm;
		while (!skm.empty()) {
			P a = skm.front();
			at(f, a) += power * znak;
			skm.pop();
			for (P dir : DIRS) {
				P b = a + dir;
				if (at(maze, b) != '#')
				if (monsters.count(b) == 0)
				if (znak > 0 || mineset.count(b) == 0)
				if (used.count(b) == 0) {
					zkm.push(b);
					used.insert(b);
				}
			}
		}
		skm = move(zkm);
		power *= 0.9; // bo tak
		power -= step;
	}
}

void assign() {
	{
	float value = 0;
	for (Expl const& e : mine) value += e.value;
	print mine.size(), "ludków, skarbów", value;
	}
	
	for (Expl & e : mine) e.assigned = false;
	ass_tr.clear();
	
	vector<P> dests;
	
	vector<vector<int>> exit_flood;
	vector<vector<int>> flood;
	
	reset_flood(exit_flood);
	for (int y : inclusive(1, HE)) for (int x : inclusive(1, WI)) {
		if (maze[y][x] == 'E') do_flood({x,y}, exit_flood);
	}
	
	map<P, vector<vector<int>>> trefloods;
	for (auto const& tr : treasures) {
		P trcoo = tr.first;
		reset_flood(trefloods[trcoo]);
		do_flood(trcoo, trefloods[trcoo]);
	}
	
	
	vector<vector<int>> cleanness;
	reset_flood(cleanness);
	
	vector<vector<float>> fajnosc;
	fajnosc.assign(HE, vector<float>(WI, 1.0)); // 1, żeby trochę zniechęcać
	{
		map<P, int> badExplorers;
		for (Oth const& oth : others) {
			badExplorers[oth.coo]++;
		}
		for (Expl const& e : mine) {
			badExplorers[e.coo]--;
		}
		for (auto const& p : badExplorers) {
			if (p.second > 0) {
				do_flood(p.first, cleanness);
			}
		}
		
		for (auto const& tr : treasures) {
			ufajnij(fajnosc, tr.first, tr.second, 0.5, 1);
		}
	}
	
	int already = 0;
	while (already < (int)mine.size()) {
		multimap<float, pair<Expl&,P>> poss;
		for (Expl & e : mine) {
			if (e.assigned) continue;
			//# odległość do każdego pola
			reset_flood(flood);
			do_flood(e.coo, flood);
			//# skarby i wyjścia
			for (auto const& tr : treasures) {
				if (tr.first.x > WI || tr.first.y > HE) continue;
				if (at(flood, tr.first) == INF) continue;
				if (ass_tr.count(tr.first)) continue;
				
				int slowbefore = e.value > e.opt_cap() ? 2 : 1;
				int dojazd = at(flood, tr.first) * slowbefore;
				
				float capa = e.capacity - e.value;
				float value_plain = min(tr.second, capa);
				
				float kara = 0;
				float const avgeat = 6;
				for (Oth const& o : others) {
					float odist = at(trefloods[tr.first], o.coo);
					if (odist < dojazd) {
						if (odist < 13) kara += avgeat;
						else {
							odist -= 13;
							if (odist < 20) kara += avgeat * odist / 20.0;
						}
					}
				}
				float value_cool = min(at(fajnosc, tr.first) - kara, capa);
				float value = (value_plain + 3*value_cool) / 4;
				
				int slowafter = e.value + value > e.opt_cap() ? 2 : 1; 
				
				int izpowrotem = dojazd + at(exit_flood, tr.first) * slowafter;
				int krecha = at(exit_flood, e.coo);
				int kosztodl = izpowrotem - krecha * slowbefore + 1;
				int czaszzapasem = izpowrotem + 5;
				
				float halfcap = e.capacity * 0.5;
				float wbocznosc = 1.5 + (halfcap - value) / (e.capacity - halfcap);
				
				if (value > 0)
				if (czaszzapasem < ttcollapse)
				if (e.value < halfcap
				||  (czaszzapasem < krecha * wbocznosc)) {
					poss.insert({value / kosztodl, {e, tr.first} });
				}
				// else if (e.value == e.capacity) {
					// value = min(tr.secound, 3*e.capacity/2 - e.value);
				// }
			}
			
			for (int y : inclusive(1, HE)) for (int x : inclusive(1, WI)) {
				if (flood[y][x] == INF) continue;
				if (maze[y][x] == 'E')
					poss.insert({-1000 - flood[y][x], {e, {x,y}} });
				float cness = cleanness[y][x];
				if (cness > 4 && e.value == 0 && 3 * flood[y][x] + 5 < ttcollapse)
					poss.insert({-flood[y][x]/cness/sqrt(cness), {e, {x,y}} });
			}
			
			//# bajeeeeery
			
			// float najfa
		}
		//# wybór tu
		if (poss.empty()) {
			print "aj!";
			for (Expl & e : mine) {
				if (!e.assigned) e.move.kind = -1;
			}
			goto zakoniec;
		}
		auto wybor = *poss.rbegin();
		Expl & e = wybor.second.first;
		P dest = wybor.second.second;
		e.assigned = true;
		if (treasures.count(dest)) ass_tr.insert(dest);
		if (e.busy == 0) {
			if (dest == e.coo) {
				if (at(maze, dest) == 'E') {
					e.move.kind = -1;
				} else if (treasures.count(dest)) {
					e.move.kind = 1;
					e.move.value = min(treasures[dest], e.capacity - e.value);
					print "!!!!!!!!", treasures[dest], e.capacity, e.value, e.move.value;
				} else {
					e.move.kind = -1;
				}
			} else {
				e.move.kind = 0;
				
				vector<vector<int>> flood;
				reset_flood(flood);
				do_flood(e.coo, flood);
				
				// print "id", e.id, "ruch", e.coo.x, e.coo.y, "do", dest.x, dest.y;
				// for (int y : inclusive(1, HE)) for (int x : inclusive(1, WI)) {
					// if (flood[y][x] != INF)
					// viz.send({ {{x,y}}, {0,0,0}, ss2s(stringstream() << flood[y][x]), -100*y-x});
				// }
				// viz.get();
				
				dests.push_back(dest);
				P fs = first_step(e.coo, dest, at(flood, dest), flood);
				assert(!(fs == P{0,0}));
				// print "fs", fs.x, fs.y;
				P dir = fs - e.coo;
				e.move.dx = dir.x;
				e.move.dy = dir.y;
			}
		} else {
			e.move.kind = -1;
		}
		already++;
	}
	
	zakoniec:
	
	static bool mryg = false;
	if (mryg) {
		viz.send({ dests, {255,255,255}, "", 99123 });
	} else {
		viz.clear(99123);
	}
	mryg ^= 1;
}

Move get_move(int id) {
	for (Expl const& e : mine) {
		if (e.id == id) return e.move;
	}
	assert(false);
}

// -------------------------------------------------
void test() {
	viz.send({ {3,2}, {255,255,0} });
	int n = in;
	print n;
}
