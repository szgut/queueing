#ifndef __KRDLN_INCLUDY_HPP__
#define __KRDLN_INCLUDY_HPP__

#include <algorithm>
#include <iostream>
#include <fstream>
#include <sstream>
#include <cassert>
#include <memory>
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
	
	#define UPlt(xx, yy) (xx) = min(xx, yy)
	#define UPgt(xx, yy) (xx) = max(xx, yy)
	
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
	
	class Print {
		ostream & os;
		bool nfirst = false;
	 public:
		Print(ostream & os = cout) : os(os) {}
		~Print() { os << endl; }
		template<class T> Print & operator , (T const& e) {
			if (nfirst) os << " "; os << e; nfirst = true; return *this; }
	};
};

#ifndef DEBUG
#define DEBUG 1
#endif
#define dprintf if (1) spacje(2), printf

#define print Print{cout},
#define prerr Print{cerr},

#endif
