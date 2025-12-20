
#include <Arduino.h>

#include "logging.h"

#define LOG_LEVEL_DISABLED	0
#define LOG_LEVEL_ERROR		1
#define LOG_LEVEL_WARN		2
#define LOG_LEVEL_INFO		3
#define LOG_LEVEL_DEBUG		4
#define LOG_LEVEL_TRACE		5

#define LOG_LEVEL LOG_LEVEL_DISABLED

namespace Logging {

	void init() {
#if LOG_LEVEL > LOG_LEVEL_DISABLED
		Serial.begin(115200);
#endif
	}

	void log(const char* log_level, const char* func_name, const char* msg) {
#if LOG_LEVEL > LOG_LEVEL_DISABLED
		Serial.printf("[%s] %s() - %s\n", log_level, func_name, msg);
#endif
	}


	void trace(const char* func_name, const char* msg) {
#if LOG_LEVEL >= LOG_LEVEL_TRACE
		Logging::log("TRACE", func_name, msg);
#endif
	}

	void debug(const char* func_name, const char* msg) {
#if LOG_LEVEL >= LOG_LEVEL_DEBUG
		Logging::log("DEBUG", func_name, msg);
#endif
	}

	void info(const char* func_name, const char* msg) {
#if LOG_LEVEL >= LOG_LEVEL_INFO
		Logging::log("INFO", func_name, msg);
#endif
	}

	void warn(const char* func_name, const char* msg) {
#if LOG_LEVEL >= LOG_LEVEL_WARN
		Logging::log("WARN", func_name, msg);
#endif
	}

	void error(const char* func_name, const char* msg) {
#if LOG_LEVEL >= LOG_LEVEL_ERROR
		Logging::log("ERROR", func_name, msg);
#endif
	}

	Trace::Trace(const char* func_name) {
#if LOG_LEVEL > LOG_LEVEL_DISABLED
		this->func_name = func_name;
		Logging::trace(this->func_name, ">");
#endif
	}
	
	Trace::~Trace() {
#if LOG_LEVEL > LOG_LEVEL_DISABLED
		Logging::trace(this->func_name, "<");
#endif
	}
};

