#ifndef __KRDLN_RANGE_HPP__
#define __KRDLN_RANGE_HPP__

namespace krdln {
	
	template <class T>
	struct Range {
		struct Intit {
			T x; Intit(T x) : x(x) {}
			T & operator * () { return x; };
			bool operator != (Intit other) { return x < other.x; }
			void operator ++ () { ++x; }
		};
		
		T b, e;
		explicit Range(T n) : b(0), e(n) {}
		Range(T b, T e) : b(b), e(e) {}
		Intit begin() { return b; }
		Intit end() { return e; }
	};
	
	template <class T>
	Range<T> range(T n) { return Range<T>(n); }
	
	template <class T>
	Range<T> range(T b, T e) { return Range<T>(b, e); }

	template <class T>
	Range<T> inclusive(T b, T e) { return Range<T>(b, e + 1); }
}

#endif
