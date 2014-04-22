#ifndef __KRDLN_IVECTOR_HPP__
#define __KRDLN_IVECTOR_HPP__

namespace krdln {
	template<class T, size_t SZ = sizeof(T*) / sizeof(T)>
	class Ivector {
		T * start;
		T * finish;
		union {
			T * end_of_space;
			T intab[SZ];
		};
		
		bool inlined() const {
			return start == intab;
		}
		
	 public:
		size_t size() const { return finish - start; }
		
		size_t capacity() const {
			if (inlined()) return SZ;
			else return end_of_space - start;
		}
		
		T * begin() { return start; }
		T const* begin() const { return start; }
		
		T * end() { return finish; }
		T const* end() const { return finish; }
		
		T & operator[] (size_t i) { return begin()[i]; }
		T const& operator[] (size_t i) const { return begin()[i]; }
		
		T & front() { return begin(); }
		T & back() { return end()[-1]; }

		explicit Ivector(size_t n = 0, T const& t = T()) {
			if (n > SZ) {
				start = new T[n];
				finish = start + n;
			} else {
				start = intab;
				finish = intab + n;
			}
			for (T & my : *this) my = t;
		}
		
		Ivector(Ivector && ivec) {
			if (ivec.start != ivec.intab) {
				start = ivec.start;
				finish = ivec.finish;
				end_of_space = ivec.end_of_space;
			} else {
				start = intab;
				finish = start;
				for (T const& e : ivec) *(finish++) = e;
			}
			ivec.start = ivec.finish = ivec.intab;
		}
		
		Ivector(Ivector const& ivec) : Ivector{} {
			for (T const& e : ivec) {
				push_back(e);
			}
		}
		
		void operator = (Ivector &&) = delete;
		
		// TODO reserve
		
		void erase(T * what) {
			for (T * ptr = what + 1; ptr != finish; ++ptr) {
				ptr[-1] = ptr[0];
			}
			finish--;
		}
		
		void push_back(T const& t) {
			if (inlined()) {
				if (finish == intab + SZ) {
					size_t new_cap = SZ ? 2 * SZ : 1;
					T * new_start = new T[new_cap];
					for (size_t i = 0; i < SZ; ++i) new_start[i] = intab[i];
					start = new_start;
					finish = start + SZ;
					end_of_space = start + new_cap;
				}
			} else {
				if (finish == end_of_space) {
					size_t new_cap = 2 * (end_of_space - start);
					T * new_start = new T[new_cap];
					T * new_finish = new_start;
					for (T * it = start; it != finish; ++it) *(new_finish++) = *it;
					delete[] start;
					start = new_start;
					finish = new_finish;
					end_of_space = new_start + new_cap;
				}
			}
			*(finish++) = t;
		}
		
		void pop_back() {
			finish--;
		}
		
		~Ivector() {
			if (!inlined()) delete[] start;
			// TODO proper drops
		}
	};
}

#endif
