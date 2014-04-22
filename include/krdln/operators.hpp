#ifndef __KRDLN_OPERATORS_HPP__
#define __KRDLN_OPERATORS_HPP__

#include <iostream>
#include <string>

namespace krdln {

#define WYPISYWALNY(TYP)                                                  \
std::ostream & operator << (std::ostream & os, TYP const& c) {            \
	bool first = true;                                                    \
	os << "{";                                                            \
	for (auto const& e : c) {                                             \
		if (first) first = false;                                         \
		else os << ", ";                                                  \
		os << e;                                                          \
	}                                                                     \
	os << "}";                                                            \
	return os;                                                            \
}

template <typename T, template<typename T> class C>
WYPISYWALNY(C<T>)

template <typename T, typename F, template<typename T, typename F> class C>
#define COMMA ,
WYPISYWALNY(C<T COMMA F>)

};

#endif
