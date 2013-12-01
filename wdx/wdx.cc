#include <krdln/includy.hpp>
#include <krdln/tcp.hpp>
#include "wdx.h"
// #include <krdln/json.hpp>
using namespace krdln;

// struct Command {
	// string action;
	// vector<vector<int>> points;
	// vector<int> color;
	// string label;
	// int tid;
	// int typ = -1;
	// int rot;
	// Command(
		// vector<vector<int>> const& pts,
		// vector<int> const& color,
		// string label = "",
		// int tid = 0
	// ) : action("add"), points(pts), color(color), tid(tid) {}
	// Command(
		// int x,
		// int y,
		// int typ,
		// int rot,
		// vector<int> const& color,
		// int tid = 0
	// ) : action("add"), points{{x,y}}, color(color), tid(tid), typ(typ), rot(rot) {}
	// Command(char const * action, int tid = 0) : action(action), tid(tid) {}
	// 
	// IMPLEMENT_JSON(Command,
		// JSON_FIELD(action),
		// JSON_FIELD(label),
		// JSON_FIELD(tid),
		// JSON_FIELD(color),
		// JSON_FIELD(points),
		// JSON_FIELD(typ),
		// JSON_FIELD(rot)
	// )
// };
// 
// struct Viz : Socket {
	// Viz() : Socket("127.0.0.1", "1234") {}
	// void send(Command const& c) {
		// string cmd = toJsonStr(c) + "\n";
		// print cmd;
		// assert(write(fd, cmd.c_str(), cmd.length())>=0);
	// }
	// vector<vector<int>> get() {
		// char buf[1005];
		// ssize_t len = read(fd, buf, 1000);
		// buf[len] = 0;
		// prerr buf;
		// assert(len > 0);
		// return {};
	// }
// };

typedef array<array<char, 4>, 4> Conni;

vector<vector<pair<int,int>>> plansza;
vector<vector<Conni>> pl_rurki;
vector<vector<bool>> pl_wet;

vector<vector<vector<int>>> vconnies = {
	{{0,0,0,0},
	 {0,0,0,0},
	 {0,0,0,0},
	 {0,0,0,0}}, // 0
	{{0,0,1,0},
	 {0,0,0,0},
	 {1,0,0,0},
	 {0,0,0,0}}, // 1
	{{0,0,1,0},
	 {0,0,0,1},
	 {1,0,0,0},
	 {0,1,0,0}}, // 2
	{{0,0,0,0},
	 {0,0,0,0},
	 {0,0,0,1},
	 {0,0,1,0}}, // 3
	{{0,1,0,0},
	 {1,0,0,0},
	 {0,0,0,1},
	 {0,0,1,0}}, // 4
	{{0,0,1,1},
	 {0,0,0,0},
	 {1,0,0,1},
	 {1,0,1,0}}, // 5
	{{0,1,1,1},
	 {1,0,1,1},
	 {1,1,0,1},
	 {1,1,1,0}}, // 6
	{{0,0,0,0},
	 {0,0,0,0},
	 {0,0,1,0},
	 {0,0,0,0}}  // 7
};

Conni v2c(vector<vector<int>> v) {
	Conni co;
	for (int r = 0; r < 4; ++r) {
		for (int c = 0; c < 4; ++c) co[r][c] = v[r][c];
	}
	return co;
}

vector<Conni> connies = [](){
	vector<Conni> ret;
	for (auto const& x : vconnies) ret.push_back(v2c(x));
	return ret;
}();

Conni cror(Conni const& co) {
	Conni wyn;
	for (int wr = 0; wr < 4; ++wr) {
		for (int wc = 0; wc < 4; ++ wc) {
			wyn[wr][wc] = co[(wr+3)%4][(wc+3)%4];
		}
	}
	return wyn;
}

bool moznaPrzykrycTo(Conni const& co, Conni const& czym) {
	for (int r = 0; r < 4; ++r) {
		for (int c = 0; c < 4; ++c) {
			if (co[r][c] == 1 && czym[r][c] == 0) return false;
		}
	}
	return true;
}

bool coHasLeg(Conni const& co, int leg) {
	for (int x : co[leg]) if (x) return true;
	return false;
}

void dumpco(Conni const& co) {
	for (auto const& r : co) {
		Print p;
		for (auto c : r) p, (int)c;
	}
	Print{};
}

void create(int xx, int yy) {
	plansza.resize(yy + 2, vector<pair<int,int>>(xx + 2, {-1,0}));
	pl_rurki.resize(yy + 2, vector<Conni>(xx+2));
	pl_wet.resize(yy + 2, vector<bool>(xx+2, false));
	for (int r = 0; r < yy + 2; ++r) {
		plansza[r][0] = {-2,0};
		plansza[r][xx+1] = {-2,0};
	}
	for (int c = 0; c < xx + 2; ++c) {
		plansza[0][c]    = {-2,0};
		plansza[yy+1][c] = {-2,0};
	}
}

bool isSureWet(int x, int y, int leg) {
	int typ = plansza[y][x].first;
	if (!pl_wet[y][x]) return false;
	if (typ == 1 || typ == 3 || typ == 5 || typ == 6 || typ == 7) {
		return coHasLeg(pl_rurki[y][x], leg);
	}
	return false;
}

bool isSureDry(int x, int y, int leg) {\
	int typ = plansza[y][x].first;
	if (typ > 0) {
		return pl_wet[y][x] == false || coHasLeg(pl_rurki[y][x], leg) == false; 
	}
	return true;
}

void put(int x, int y, int typ, int rot, bool wet) {
	plansza[y][x] = {typ, rot};
	if (typ > 0) {
		Conni co = connies[typ];
		while (rot--) co = cror(co);
		pl_rurki[y][x] = co;
	}
	pl_wet[y][x] = wet;
}

struct Dge {
	int len;
	int x, y, leg;
	bool operator < (Dge const& dge) const {
		return tie(len,x,y,leg) < tie(dge.len, dge.x, dge.y, dge.leg);
	}
	Dge go() const {
		if (leg == 0) return {len, x + 1, y, leg^2};
		if (leg == 2) return {len, x - 1, y, leg^2};
		if (leg == 1) return {len, x, y + 1, leg^2};
		if (leg == 3) return {len, x, y - 1, leg^2};
		assert(false);
	}
	Dge withLeg(int leg) const {
		return {len,x,y,leg};
	}
	Dge withLen(int len) const {
		return {len,x,y,leg};
	}
};

Wybory ask(int x, int y) {
	set< tuple<int,int,int> > ziels;
	map< tuple<int,int,int>, int > bests; 
	map< tuple<int,int,int>, pair<int,int> > how;
	map< tuple<int,int,int>, tuple<int,int,int> > from;
	set<Dge> skm;
	for (int leg = 0; leg < 4; ++leg) {
		skm.insert(Dge{0, x, y, leg});
	}
	while (!skm.empty()) {
		Dge d = *skm.begin();
		skm.erase(skm.begin());
		// print d.len, d.x, d.y, d.leg, "SKM_pre";
		if (plansza[d.y][d.x].first == -2) continue; // ściany
		// print d.len, d.x, d.y, d.leg, "SKM";
		for (int t = 0; t < 6; ++t) {
			Conni conni = connies[t];
			for (int rot = 0; rot < 4; ++rot, conni = cror(conni)) {
				if (!moznaPrzykrycTo(pl_rurki[d.y][d.x], conni)) break;
				// print "  można przykryć przez", t, rot;
				bool ok = true;
				for (int leg = 0; leg < 4; ++leg) if (coHasLeg(conni, leg)) {
					Dge back = d.withLeg(leg).go();
					if (!isSureDry(back.x, back.y, back.leg)) {
						for (int leg2 = 0; leg2 < 4; ++leg2) if (conni[leg][leg2]) {
							Dge back2 = d.withLeg(leg2).go();
							if (!isSureDry(back2.x, back2.y, back2.leg))
								ok = false; // cykl
						}
					}
				}
				if (!ok) break;
				// print "   nie ma cylku";
				for (int leg = 0; leg < 4; ++leg) if (conni[d.leg][leg]) {
					// print "   leg", leg;
					Dge back = d.withLeg(leg).go();
					tuple<int,int,int> triple{back.x, back.y, back.leg};
					tuple<int,int,int> maple{d.x, d.y, d.leg};
					if (isSureWet(back.x, back.y, back.leg)) {
						ziels.insert(triple);
						// print "     mokro";
					}
					// print "WTF";
					int nlen = d.len + 1;
					if (bests.count(triple)) {
						int oldbest = bests[triple];
						if (nlen < oldbest) {
							// print "       nadpis";
							bests[triple] = nlen;
							skm.erase(back.withLen(oldbest));
							skm.insert(back.withLen(nlen));
							from[triple] = maple;
							how[triple] = {t, rot};
						}
					} else {
						// print "dopis";
						// print " ", d.x, d.y, t, rot;
						// print back.len, back.x, back.y, back.leg;
						bests[triple] = nlen;
						skm.insert(back.withLen(nlen));
						from[triple] = maple;
						how[triple] = {t, rot};
					}
				}
			}
		}
	}
	int mici = 2000;
	tuple<int,int,int> tam;
	for (auto const& tup : ziels) {
		if (bests[tup] < mici) {
			mici = bests[tup];
			tam = tup;
		}
	}
	if (mici == 2000) return {{}};
	vector<pair< pair<int,int>, pair<int,int> >> wyn;
	do {
		if (!from.count(tam)) break; // awaryjnie
		auto jak = how[tam];
		tam = from[tam];
		int xx, yy, leg;
		tie(xx, yy, leg) = tam;
		wyn.push_back({{xx,yy}, jak});
	} while (get<0>(tam) != x || get<1>(tam) != y);
	return {wyn};
}

// 
// int main() {
	// Viz viz;
	// auto add = [&] (int x, int y, int typ, int rot, bool wet) {
		// static int licz = 0;
		// licz++;
		// auto color = wet ? vector<int>{100,200,200} : vector<int>{50,200,80};
		// viz.send(Command(x, y, typ, rot, color, licz));
		// put(x, y, typ, rot, wet);
	// };
	// 
	// #define WI 5
	// #define HE 5
	// 
	// create(WI, HE);
	// vector<vector<int>> sciany;
	// for (int r = 0; r < HE + 2; ++r) {
		// for (int c = 0; c < WI + 2; ++c) {
			// if (plansza[r][c].first == -2) {
				// sciany.push_back({c,r});
			// }
		// }
	// }
	// viz.send(Command(sciany, {50,50,50}));
	// 
	// add(2, 2, 6, 0, true);
	// auto dxret = ask(4, 4);
	// for (auto const& yyy : dxret) {
		// add(yyy.first.first, yyy.first.second, yyy.second.first, yyy.second.second, false);
	// }
	// print "dxok", dxret.size();
	// while (true);
	// 
	// dumpco(cror(connies[3]));
	// 
	// return 0;
// }
