#ifndef __KRDLN_JSON_HPP__
#define __KRDLN_JSON_HPP__

#include <string>
#include <jansson.h> // -ljansson
namespace krdln {

// fromJson-------------------------------------------------------------

template<class T> T fromJson(json_t * json);

// obj
void fieldsFromJson(json_t *) {}

template<class T, class... A>
void fieldsFromJson(json_t * json, char const* key, T & field, A&... rest) {
	json_t * jfield = json_object_get(json, key);
	assert(jfield);
	field = fromJson<T>(jfield);
	fieldsFromJson(json, rest...);
}

template<class T>
struct FromJson { T operator() (json_t * json) { return T(json); } };

template<class T>
T fromJson(json_t * json) { return FromJson<T>{}(json); }

// int
template<>
struct FromJson<int>{ int operator() (json_t * json) {
	assert(json_is_integer(json));
	return json_integer_value(json);
}};

// real
template<>
struct FromJson<double>{ double operator() (json_t * json) {
	assert(json_is_number(json));
	return json_number_value(json);
}};

// str
template<>
struct FromJson<std::string>{ std::string operator() (json_t * json) {
	assert(json_is_string(json));
	return json_string_value(json);
}};

// arr
template<class T>
struct FromJson<vector<T>>{ vector<T> operator() (json_t * json) {
	assert(json_is_array(json));
	vector<T> ret;
	ret.reserve(json_array_size(json));
	size_t id; json_t * val;
	json_array_foreach(json, id, val) {
		ret.push_back(fromJson<T>(val));
	}
	return ret;
}};

// fromJsonStr ---------------------------------------------------------

template<class T> T fromJsonStr(char const * str) {
	json_error_t jerr;
	json_t * json{json_loads(str, 0, &jerr)};
	assert(json);
	T ret = fromJson<T>(json);
	json_decref(json);
	return ret;
}

template<class T> T fromJsonBuf(char const * buf, size_t len) {
	json_error_t jerr;
	json_t * json{json_loadb(buf, len, 0, &jerr)};
	assert(json);
	T ret = fromJson<T>(json);
	json_decref(json);
	return ret;
}

// toJson --------------------------------------------------------------

template<class T> json_t * toJson(T const&);

// obj
template<class T>
struct ToJson { json_t * operator() (T const& obj) {
	return obj.toJson();
}};

template<class T> json_t * toJson(T const& obj) {
	return ToJson<T>{}(obj);
}

json_t * fieldsToJson() {
	return json_object();
}

template<class T, class... A>
json_t * fieldsToJson(char const * key, T const& field, A const&... rest) {
	json_t * obj = fieldsToJson(rest...);
	json_object_set_new(obj, key, toJson<T>(field));
	return obj;
}

// int
template<>
struct ToJson<int> { json_t * operator() (int x) {
	return json_integer(x);
}};

// real
template<>
struct ToJson<double> { json_t * operator() (double x) {
	return json_real(x);
}};

// str
template<>
struct ToJson<std::string> { json_t * operator() (std::string const& x) {
	return json_string(x.c_str());
}};

// arr
template<class T>
struct ToJson<vector<T>> { json_t * operator() (vector<T> const& v) {
	json_t * ja = json_array();
	for (T const& x : v) {
		json_array_append_new(ja, toJson<T>(x));
	}
	return ja;
}};

// toJsonStr -----------------------------------------------------------

template<class T> std::string toJsonStr(T const& obj) {
	json_t * json = toJson<T>(obj);
	char * str = json_dumps(json, 0);
	std::string ret{str};
	free(str);
	json_decref(json);
	return ret;
}

// whoa ----------------------------------------------------------------

#define JSON_FIELD(x) #x, x
#define IMPLEMENT_JSON(T, ...) \
	T(json_t * json) { fieldsFromJson(json, __VA_ARGS__); } \
	json_t * toJson() const { return fieldsToJson(__VA_ARGS__); }

// ---------------------------------------------------------------------

} // namespace krdln

#endif
