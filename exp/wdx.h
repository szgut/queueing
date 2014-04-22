#include <vector>

struct Move {
	int dx, dy;
	int kind;
	int weapon;
	float value;
};

void set_dims(int wi, int he);
void push_row(char const* str);

void clear_treasures();
void add_treasure(int x, int y, float v);

void clear_monsters();
void add_monster(int x, int y, int a, float v);

void clear_others();
void add_other(int x, int y, int a);

void clear_mine();
void add_mine(
	int id, int x, int y, int attack, float weapon, int monsters,
	float value, float capacity, int busy
	);

void set_ttc(int x);

void assign();
Move get_move(int id);

void paint();

void test();
