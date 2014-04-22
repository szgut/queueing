#ifndef __KRDLN_SPLIT_HPP__
#define __KRDLN_SPLIT_HPP__

#include <cstddef>
#include <cstdio>

namespace krdln {
	template<class C, class F>
	class Split;
	
	template<class C, class F>
	class Spliterator {
		typedef typename C::iterator Iter;
		
		F f;
		Iter begin_, end_, endend;
		size_t size_;
		
		void init() {
			Iter left = begin_;
			if (end_ != endend) ++end_, ++size_;
			while (end_ != endend) {
				if (f(*left, *end_)) {
					++size_;
					left = end_;
					++end_;
				}
				else break;
			}
		}
		
		explicit Spliterator(Iter const& bb, Iter const& ee, F fun) :
			f(fun), begin_(bb), end_(bb), endend(ee), size_(0) {
			init();
		}
		
		friend class Split<C,F>;
		
	 public:
		typedef typename C::value_type value_type;
		
		Iter begin() const { return begin_; }
		Iter end() const { return end_; }
		size_t size() const { return size_; }
		void operator ++ () { begin_ = end_; size_ = 0; init(); }
		bool operator != (Spliterator const& right) const { return begin() != right.begin(); }
		
		/// sam sobie sterem...
		Spliterator & operator * () { return *this; }
		Spliterator * operator -> () { return this; }
	};
	
	template<class C, class F>
	class Split {
				
		C & cont;
		F fun;
		
	 public:
		typedef Spliterator<C,F> value_type;
		
		explicit Split(C & cont, F const& fun) : cont(cont), fun(fun) {}
		value_type begin() { return value_type(cont.begin(), cont.end(), fun); }
		value_type end() { return value_type(cont.end(), cont.end(), fun); }
	};

	template<class C, class F>
	Split<C,F> split(C & cont, F const& fun) { return Split<C,F>(cont, fun); }
}

#endif
