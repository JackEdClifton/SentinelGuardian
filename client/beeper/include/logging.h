#pragma once

namespace Logging {

	void init();

	void trace(const char* func_name, const char* msg);
	void debug(const char* func_name, const char* msg);
	void info(const char* func_name, const char* msg);
	void warn(const char* func_name, const char* msg);
	void error(const char* func_name, const char* msg);

	class Trace {
		const char* func_name;
	public:
		Trace(const char* func_name);
		~Trace();
	};
};



