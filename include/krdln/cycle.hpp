#ifndef __KRDLN_CYCLE_HPP__
#define __KRDLN_CYCLE_HPP__

namespace krdln {
	unsigned long long cycleCount() {
		unsigned lo, hi;
		/* We cannot use "=A", since this would use %rax on x86_64 */
		asm volatile ("rdtsc" : "=a" (lo), "=d" (hi));
		return (unsigned long long)hi << 32 | lo;
	}
}

#endif
