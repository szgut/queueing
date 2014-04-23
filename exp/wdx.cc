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

volatile bool animate = true;

struct Viz : Socket {
	Viz() : Socket("127.0.0.1", "1234") {}
	
	void clear(int tid) {
		send({ {}, {0,0,0}, "", tid});
	}
	
	void send(Command const& c) {
		if (animate) {
			string cmd = toJsonStr(c) + "\n";
			// print cmd;
			assert(write(fd, cmd.c_str(), cmd.length())>=0);
		}
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

struct Eq {
	int id;
	float price;
	int attack;
	float weight;
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
	P smok;
	
	float capa() const {
		return capacity - value - weapon;
	}
	
	float opt_cap() const {
		return capacity * 2 / 3;
	}
	
	int slowness() const {
		return value > opt_cap() ? 2 : 1;
	}
	
	Expl(int id, int x, int y, int a, float w, int m, float v, float c, int b) :
		id(id), coo{x,y}, attack(a), weapon(w), monsters(m), value(v), capacity(c), busy(b), smok{0,0}
	{}
};

vector<string> maze;
map<P, float> treasures;
set<P> ass_tr;
map<P, Mon> monsters;
vector<Expl> mine;
set<P> mineset;
vector<Oth> others;
vector<Eq> equipment;
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

void clear_eq() {
	equipment.clear();
}

void add_eq(int id, float price, int attack, float weight) {
	equipment.push_back({id, price, attack, weight});
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

void do_flood(P start, vector<vector<int>> & v, int moc = 1) {
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
				if (monsters.count(b) == 0 || monsters[b].attack < moc)
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
	static bool mryg = false;
	{
	float value = 0;
	for (Expl const& e : mine) value += e.value;
	print mine.size(), "ludków, skarbów", value;
	}
	
	for (Expl & e : mine) {
		e.assigned = false;
		e.smok = {0,0};
	}
	ass_tr.clear();
	
	vector<P> dests;
	vector<P> smoki;
	
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
		vector<P> maximas;
		for (int y : inclusive(1, HE)) for (int x : inclusive(1, WI)) {
			P a = {x,y};
			int cness = at(cleanness, a);
			if (cness == INF) continue;
			bool ismax = true;
			for (P dir : DIRS) {
				P b = a + dir;
				if (at(cleanness, b) == INF) continue;
				if (at(cleanness, b) > cness) ismax = false;
			}
			if (ismax) maximas.push_back(a);
		}
		for (P p : maximas) {
			do_flood(p, cleanness);
		}
		
		for (auto const& tr : treasures) {
			ufajnij(fajnosc, tr.first, tr.second, 0.5, 1);
		}
	}
		
	map<P, vector<vector<int>>> afloods;
	for (int y : inclusive(1, HE)) for (int x : inclusive(1, WI)) {
		if (maze[y][x] == 'A') {
			P armcoo = {x,y};
			reset_flood(afloods[armcoo]);
			do_flood(armcoo, afloods[armcoo]);
		}
	}
	
	int already = 0;
	while (already < (int)mine.size()) {
		multimap<float, pair<Expl&,P>> poss;
		for (Expl & e : mine) {
			if (e.assigned) continue;
			//# odległość do każdego pola
			reset_flood(flood);
			do_flood(e.coo, flood, e.attack);
			//# skarby i wyjścia
			
			for (auto const& tr : treasures) {
				if (tr.first.x > WI || tr.first.y > HE) continue;
				if (at(flood, tr.first) == INF) continue;
				if (ass_tr.count(tr.first)) continue;
				
				int slowbefore = e.value > e.opt_cap() ? 2 : 1;
				int dojazd = at(flood, tr.first) * slowbefore;
				
				float value_plain = min(tr.second, e.capa());
				
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
				float value_cool = min(at(fajnosc, tr.first) - kara, e.capa());
				float value = (value_plain + 3*value_cool) / 4;
				
				int slowafter = e.value + value > e.opt_cap() ? 2 : 1; 
				
				int izpowrotem = dojazd + at(exit_flood, tr.first) * slowafter;
				int krecha = at(exit_flood, e.coo);
				int kosztodl = izpowrotem - krecha * slowbefore + 1;
				int czaszzapasem = izpowrotem + 5;
				
				float halfcap = e.capacity * 0.5;
				float wbocznosc = 1.5 + (halfcap - value) / (e.capacity - halfcap);
				
				if (value > 0)
				if (czaszzapasem * 1.2 < ttcollapse)
				if (e.value < halfcap
				||  (czaszzapasem < krecha * wbocznosc)) {
					poss.insert({value / kosztodl, {e, tr.first} });
				}
			}
			
			float best_clear = -INF;
			P best_clear_dest = {0,0};
			for (int y : inclusive(1, HE)) for (int x : inclusive(1, WI)) {
				if (flood[y][x] == INF) continue;
				if (maze[y][x] == 'E')
					poss.insert({-1000 - flood[y][x], {e, {x,y}} });
				float cness = cleanness[y][x];
				if (cness > 4 && e.value == 0 && 2*flood[y][x] + 3*exit_flood[y][x] + 5 < ttcollapse) {
					float maybe = -flood[y][x]/cness/sqrt(cness)/sqrt(exit_flood[y][x]);
					if (maybe > best_clear) {
						best_clear = maybe;
						best_clear_dest = {x,y};
					}
				}
			}
			if (best_clear_dest != P{0,0}) {
				poss.insert({best_clear, {e, best_clear_dest}});
			}
			
			//# smoczy pomocnicy
			// if (e.value == 0) {
				// for (Expl const& lowca : mine) {
					// if (lowca.smok != P{0,0})
					// for (P dir : DIRS) {
						// P b = lowca.smok + dir;
						// if (at(flood, b) != INF) {
							// int time = at(flood, b) + at(exit_flood, lowca.smok) * 2 + 5;
							// if (time * 1.2f < ttcollapse)
								// poss.insert({ 10.0f / time, {e, b} });
						// }
					// }
				// }
			// }
		}
		
		for (auto const& mp : monsters) {
			
			int mattack = mp.second.attack;
			P mcoo = mp.first;
			if (mcoo.x > WI || mcoo.y > HE) continue;
			if (ass_tr.count(mcoo)) continue;
			
			vector<vector<int>> mflood;
			reset_flood(mflood);
			do_flood(mcoo, mflood);
			
			int escape_dist = INF;
			for (int y : inclusive(1, HE)) for (int x : inclusive(1, WI)) {
				if (maze[y][x] == 'Y') UPlt(escape_dist, mflood[y][x]);
			}
			if (escape_dist == INF) continue;
			
			float trval = mp.second.value;
			{
				float trvaladd = 0;
				for (P dir : DIRS) {
					P b = mcoo + dir;
					if (at(maze, b) != '#' && at(cleanness, b) == INF) {
						trvaladd = max(trvaladd, at(fajnosc, b));
					}
				}
				trval += trvaladd;
			}
			
			float bestsmok = 0;
			Expl * beste = &*mine.begin();
			P smodest = {0,0};
			for (Expl & e : mine) {
				if (at(mflood, e.coo) == INF) continue;
				if (e.attack > mattack) {
					int time = e.slowness() * at(mflood, e.coo) + 2 * escape_dist;
					float afterweight = e.value;
					if (e.monsters == 2) afterweight += e.weapon;
					float leftca = e.capacity * 1.1f - afterweight;
					float value = min(leftca + 10.0f, trval);
					
					float score = value/time;
					if (time * 1.2f < ttcollapse)
					if (score > bestsmok) {
						beste = &e;
						bestsmok = score;
						smodest = mcoo;
					}
					
				} else if (e.attack == 1) {
					for (auto const& eq : equipment) {
						if (eq.attack <= mattack) continue;
						if (eq.price > e.value) continue;
						float afterweight = e.value - eq.price + eq.weight;
						if (afterweight > e.capacity) continue;
						float afterslow = afterweight > e.opt_cap() ? 2 : 1;
						float leftca = e.capacity * 1.1f - afterweight;
						for (auto const& arr : afloods) {
							if (at(mflood, arr.first) == INF) continue;
							int time =
								e.slowness() * at(arr.second, e.coo)
								+ afterslow * at(mflood, arr.first)
								+ 2 * escape_dist
							;
							float value = min(leftca + 10.0f, trval);
							
							float score = value/time;
							if (time * 1.2f < ttcollapse)
							if (score > bestsmok) {
								beste = &e;
								bestsmok = score;
								e.move.weapon = eq.id;
								smodest = arr.first;
							}
						}
					}
				}
			}
			if ((int)mine.size() > 7 && bestsmok != 0 && already == 0) {
				poss.insert({ 4.2f + bestsmok, {*beste, smodest} });
				smoki.push_back(beste->coo);
				smoki.push_back(smodest);
			}
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
		if (treasures.count(dest) || monsters.count(dest)) ass_tr.insert(dest);
		if (monsters.count(dest)) e.smok = dest;
		// if (!treasures.count(dest) && !monsters.count(dest)
		 // && !(at(maze, dest) == 'E') && !(at(maze, dest) == 'A')) {
			do_flood(dest, cleanness, e.attack);
		// }
		if (e.busy == 0) {
			if (dest == e.coo) {
				if (at(maze, dest) == 'E') {
					e.move.kind = -1;
				} else if (treasures.count(dest)) {
					e.move.kind = 1;
					e.move.value = min(treasures[dest], e.capa());
					// print "!!!!!!!!", treasures[dest], e.capacity, e.value, e.move.value;
				} else if (monsters.count(dest)) {
					e.move.kind = 1;
					e.move.value = min(treasures[dest], e.capa());
					// print "!!!!!!!!", treasures[dest], e.capacity, e.value, e.move.value;
				} else if (at(maze, dest) == 'A') {
					e.move.kind = 3;
					print "kupuje łepon", e.move.weapon;
					//# weapon już ustawiony
				} else {
					e.move.kind = -1;
				}
			} else {
				e.move.kind = 0;
				
				vector<vector<int>> flood;
				reset_flood(flood);
				do_flood(e.coo, flood, e.attack);
				
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
	
	if (mryg) {
		viz.send({ smoki, {255,255,0}, "", 99125});
		viz.send({ dests, {255,255,255}, "", 99123 });
	} else {
		viz.clear(99123);
		viz.clear(99125);
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
