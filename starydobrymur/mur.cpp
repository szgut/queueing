#include <algorithm>
#include <iostream>
#include <fstream>
#include <cassert>
#include <vector>
#include <cstdio>
#include <array>
#include <deque>
#include <cmath>
#include <stack>
#include <queue>
#include <set>
#include <map>
namespace {
	using namespace std;

	typedef vector<int> vint;
	typedef long long unsigned ulo;
	typedef long long lint;
	
	void spacje(int k) {
		int magic;
		static stack<int*> stos;
		while (!stos.empty() && stos.top() <= &magic) stos.pop();
		stos.push(&magic);
		for (int n = k * stos.size(); n--;) printf(" ");
	}
	
	#define BOTH(x) for (int x = 0; x < 2; ++x)
	
	#define UPlt(xx, yy) (xx) = ::min(xx, yy)
	#define UPgt(xx, yy) (xx) = ::max(xx, yy)
	
	struct in_t {
		template<class T>
		operator T () {
			static bool __attribute__((unused)) dummy = ios_base::sync_with_stdio(false);
			T x;
			cin >> x;
			return x;
		}
	};
	in_t __attribute__((unused)) in;
};

#ifndef DEBUG
#define DEBUG 1
#endif
#define dprintf if (1) spacje(2), printf


typedef unsigned uns;

struct Matrix {
	size_t wi;
	size_t he;
	vector<short> v;
	
	Matrix(uns wi, uns he, in_t) : wi(wi), he(he), v(wi*he) {
		for (auto & x : v) x = in;
	}
	Matrix(uns wi, uns he, short x) : wi(wi), he(he), v(wi*he, x) {}
	short & operator() (uns y, uns x) { return v[y * wi + x]; }
	short operator() (uns y, uns x) const { return v[y * wi + x]; }
	
	vector<int> operator * (vector<int> const& v) const {
		assert(v.size() == wi);
		vector<int> wynik(he, 0);
		for (uns i = 0; i < he; ++i) {
			for (uns j = 0; j < wi; ++j) wynik[i] += (*this)(i, j) * v[j];
		}
		return wynik;
	}
	
	bool operator < (Matrix const& b) const { return v < b.v; }
	
	Matrix & operator += (Matrix const& m) {
		assert(wi == m.wi && he == m.he);
		for (uns i = 0; i < v.size(); ++i) v[i] += m.v[i];
		return *this;
	}
	
	Matrix & operator -= (Matrix const& m) {
		assert(wi == m.wi && he == m.he);
		for (uns i = 0; i < v.size(); ++i) v[i] -= m.v[i];
		return *this;
	}
	
	Matrix & operator *= (int x) { for (auto & e : v) e *= x; return *this; }
	
	Matrix operator + (Matrix const& m) const { return Matrix(*this) += m; }
	Matrix operator - (Matrix const& m) const { return Matrix(*this) -= m; }
	Matrix operator * (int x) const { return Matrix(*this) *= x; }
	
	uns sum() const {
		uns sum = 0;
		for (auto const& x: v) sum += x;
		return sum;
	}
	
	Matrix slice(uns y0, uns x0, uns de) const {
		Matrix wyn{de, de, 0};
		for (uns y = 0; y < de; ++y) {
			for (uns x = 0; x < de; ++x) {
				wyn(y, x) = (*this)(y0 + y, x0 + x);
			}
		}
		return wyn;
	}
	
	int max() const {
		int mx = -10;
		for (int x : v) UPgt(mx, int(x));
		return mx;
	}
	
	friend ostream & operator << (ostream & os, Matrix const& m) {
		os << "______" << endl;
		for (uns r = 0; r < m.he; ++r) {
			for (uns c = 0; c < m.wi; ++c) os << " " << m(r,c);
			os << endl;
		}
		return os;
	}
};

struct Box {
	size_t de;
	vector<Matrix> v;
	
	Box(){}
	
	Box(uns wi, uns he, uns de, in_t) : de(de) {
		for (size_t z = 0; z < de; ++z) {
			v.emplace_back(wi, he, in);
		}
	}
	Box(uns wi, uns he, uns de, short x) : de(de), v(de, {wi, he, x}) {}
	short & operator() (uns z, uns y, uns x) { return v[z](y,x); }
	short operator() (uns z, uns y, uns x) const { return v[z](y,x); }
	
	bool operator < (Box const& b) const { return v < b.v; }
	
	uns volume() const {
		uns sum = 0;
		for (auto const& x: v) sum += x.sum();
		return sum;
	}
	
	friend ostream & operator << (ostream & os, Box const& b) {
		os << "===" << endl;
		for (auto const& x : b.v) os << x << endl;
		return os;
	}
	
	Box rot(Matrix const& rotator) {
		Box box(de, de, de, 0);
		for (uns z = 0; z < de; ++z)
			for (uns y = 0; y < de; ++y)
				for (uns x = 0; x < de; ++x) {
					// ~cerr << endl << endl << rots[rid] << endl;
					// ~cerr << x << " " << y << " " << z << endl;
					vector<int> ret = rotator * vector<int>{{2*int(x),2*int(y),2*int(z),1}};
					// ~cerr << ret[0] << " " << ret[1] << " " << ret[0] << endl;
					box(ret[2]>>1, ret[1]>>1, ret[0]>>1) = (*this)(z,y,x);
				}
		return box;
	}
};

struct Klocek {
	uns id;
	float weight;
	float pmin;
	Box b;
	Klocek(uns de, in_t) : id(in), weight(in), pmin(in), b(de, de, de, in) {}
};

typedef tuple<float, uns, uns, uns, uns, float, uns> E;

int main() {
	cerr << "wczytuję" << endl;
	
	float Cv = in, Cp = in;
	uns X = in, Y = in, Z = in;
	Matrix above(X + 2, Y + 2, in);	
	
	uns D = in;
	uns nshapes = in;
	vector<Klocek> shapes;
	
	map<uns, Box> m;
	while (nshapes--) {
		shapes.emplace_back(D, in);
		m[shapes.back().id] = shapes.back().b;
	}
	
	vector<Matrix> rots;
	for (int n = 24; n--; ) rots.emplace_back(4, 4, in);
	
	//
	
	cerr << "liczę" << endl;
	
	vector<E> elems;
	for (Klocek & k : shapes) {
		set<Box> skm;
		for (uns rid = 0; rid < 24; ++rid) {
			Box box = k.b.rot(rots[rid]);
			if (skm.insert(box).second == false) continue;
			
			Matrix himap(D, D, 0);
			Matrix shadow(D, D, 0);
			for (uns z = 0; z < D; ++z) {
				for (uns y = 0; y < D; ++y) {
					for (uns x = 0; x < D; ++x) {
						if (box(z,y,x)) shadow(y, x) = 1;
						if (! shadow(y, x)) himap(y,x)++;
					}
				}
			}
			himap = himap + (Matrix{D, D, 1} - shadow) * Z;
			
			for (int y = 1; y <= int(Y - D + 1); ++y) {
				for (int x = 1; x <= int(X - D + 1); ++x) {
					uns h0 = (above.slice(y, x, D) - himap).max() + 1;
					// ~cerr << box << himap << above.slice(y, x, D) << h0 << endl << endl;
					static const vector<tuple<int,int,int>> szesc = {
						tuple<int,int,int>{-1,0,0},
						tuple<int,int,int>{1,0,0},
						tuple<int,int,int>{0,1,0},
						tuple<int,int,int>{0,-1,0},
						tuple<int,int,int>{0,0,-1}
					};
					float taczes = 0;
					if (D <= 3) {
						const static vector<float> MAYBE = {1.f/D, 0.5f/D, 0.25f/D, 0.125f/D};
						for (int zz = 0; zz < int(D); ++zz) {
							for (int yy = 0; yy < int(D); ++yy) {
								for (int xx = 0; xx < int(D); ++xx) {
									if (box(zz,yy,xx)) {
										for (auto const& dir : szesc) {
											int dx, dy, dz;
											tie(dx, dy, dz) = dir;
											int nx = x + xx + dx;
											int ny = y + yy + dy;
											int nz = h0 + zz + dz;
											if (above(ny, nx) == nz) taczes++;
											else if (
												above(ny, nx) > nz &&
												above(ny, nx) <= nz + 4 
											) taczes += MAYBE.at(above(ny, nx) - nz - 1);
										}
									}
								}
							}
						}
					} else {
						int itaczes = 0;
						for (int zz = 0; zz < int(D); ++zz) {
							for (int yy = 0; yy < int(D); ++yy) {
								for (int xx = 0; xx < int(D); ++xx) {
									if (box(zz,yy,xx)) {
										for (auto const& dir : szesc) {
											int dx, dy, dz;
											tie(dx, dy, dz) = dir;
											int nx = x + xx + dx;
											int ny = y + yy + dy;
											int nz = h0 + zz + dz;
											taczes += above(ny,nx) == nz;
										}
									}
								}
							}
						}
						taczes = itaczes;
					}
					// ~cerr << taczes << endl;
					if (taczes >= k.pmin && h0 + D <= Z) {
						float score = k.weight * (Cv * box.volume() + Cp * taczes);
						elems.emplace_back(-score, k.id, rid, x, y, taczes, h0);
					}
				}
			}
		}
	}
	
	cerr << "sorcę" << endl;
	sort(elems.begin(), elems.end());
	if (elems.size() > 666) elems.resize(666);
	cerr << "wypisuję" << endl;
	cout << elems.size() << endl;
	// ~int piec = 1;
	for (E const& e : elems) {
		float score, taczes;
		uns id, rid, x, y, h0;
		tie(score, id, rid, x, y, taczes, h0) = e;
		
		// ~if (piec) {
			// ~piec--;
			// ~cerr << m[id] << " " << m[id].rot(rots[rid]) << endl;
			// ~cerr << x << " " << y << "    taczes " << taczes << "     h0 " << h0 << endl;
			// ~cerr << above.slice(y-1, x-1, 4) << endl;
		// ~}
		
		cout << -score << " " << id << " "<< rid << " " <<  (x-1) << " " << (y-1) << endl;
		//w pythu mam indeksowanie od 0
	}
	
	return 0;
}
