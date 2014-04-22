#ifndef __KRDLN_OPTARG_HPP__
#define __KRDLN_OPTARG_HPP__

//~ 
	//~ char c;
	//~ while (~(c=getopt(argc, argv, "a:P:C:p:f:R:n:"))) {
		//~ switch(c) {
			//~ case 'a': MCAST_ADDR = optarg; break;
			//~ case 'P': tryd(sscanf, optarg, "%d", &DATA_PORT);  break;
			//~ case 'C': tryd(sscanf, optarg, "%d", &CTRL_PORT); break;
			//~ case 'p': tryd(sscanf, optarg, "%d", &PSIZE); break;
			//~ case 'f': tryd(sscanf, optarg, "%d", &FSIZE); break;
			//~ case 'R': tryd(sscanf, optarg, "%d", &RTIME); break;
			//~ case 'n': NAZWA = optarg; break;
			//~ default: return 1;
		//~ }
	//~ }

#include <cstdio>
#include <vector>
#include <string>
#include <unistd.h>
#include <sstream>
#include <iostream>

namespace krdln {

class Option;

class Options {
    std::vector<Option *> vec;
    
    friend class Option;
    bool internal_eval(int argc, char * const * argv);
 public:
    bool eval(int argc, char * const * argv);
};

class Option {
 protected:
    char letter;
    char const * descr;
    
    virtual bool handle(char const * optarg) = 0;
    virtual bool colon() = 0;
    virtual void describe(std::ostream & os) = 0;
    virtual bool is_ready() = 0;
    
    friend class Options;
 public:
    Option(Options * where, char letter, char const * descr)
            : letter(letter), descr(descr) {
        where->vec.push_back(this);
    }
};

template<typename T>
class ArgOption : public Option {
    bool required;
    bool ready;
    T def;
    T value;
    Options * where;
    
    bool handle(char const * optarg) {
        std::stringstream ss(optarg);
        ss >> value;
        return (ready = bool(ss));
    }
    
    bool colon() {
        return true;
    }
    
    void describe(std::ostream & os) {        
        os << " -" <<  letter << " " << descr;
        if (required) os << " -- required\n";
        else os << " -- default " << def << std::endl;
    }
    
    bool is_ready() { return ready; }
    
 public:
    ArgOption(Options * where, char letter, T def, char const * descr)
            : Option(where, letter, descr), required(false), def(def) {
        value = def;
        ready = !required;
    }
    ArgOption(Options * where, char letter, char const * descr)
            : Option(where, letter, descr), required(true) {
        ready = !required;
    }
    operator T () {
        return value;
    }
};

class BoolOption : Option {
    bool value;
    
    bool handle(char const *) {
        value = true;
        return true;
    }
    
    bool colon() { return false; }
    
    void describe(std::ostream & os) {
        os << " -" << letter << " -- " <<  descr << std::endl;
    }
    
    bool is_ready() { return true; }
    
 public:
    BoolOption(Options * where, char letter, char const * descr)
            : Option(where, letter, descr), value(false) {}
            
    operator bool () {
        return value;
    }
};

bool Options::internal_eval(int argc, char * const * argv) {
    std::string optstring;
    for (Option * o : vec) {
        optstring.push_back(o->letter);
        if (o->colon()) optstring.push_back(':');
    }
    
    char c;
    while (~(c=getopt(argc, argv, optstring.c_str()))) {
        bool handled = false;
        for (Option * o : vec) {
            if (o->letter == c) {
                if (o->handle(optarg)) {
                    handled = true;
                    break;
                } else {
                    return false;
                }
            }
        }
        if (!handled) return false;
    }
    for (Option * o : vec) {
        if (!o->is_ready()) {
            fprintf(stderr, "Option '%c' is required\n", o->letter);
            return false;
        }
    }
    return true;
}

bool Options::eval(int argc, char * const * argv) {
    if (internal_eval(argc, argv)) return true;
    else {
        std::cerr << "Options:\n";
        for (Option * o : vec) {
            o->describe(std::cerr);
        }
        return false;
    }
}

}

#endif
