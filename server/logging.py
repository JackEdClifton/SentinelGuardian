
import inspect
import datetime

# Log levels
LOG_LEVEL_DISABLED = 0
LOG_LEVEL_ERROR    = 1
LOG_LEVEL_WARN     = 2
LOG_LEVEL_INFO     = 3
LOG_LEVEL_DEBUG    = 4
LOG_LEVEL_TRACE    = 5

# Set desired log level here
LOG_LEVEL = LOG_LEVEL_TRACE

def _caller_name(depth=2) -> str:
	frame = inspect.currentframe()
	try:
		return frame.f_back.f_back.f_code.co_name
	finally:
		del frame



class Logging:

	def _log(log_level: str, msg: str):
		if LOG_LEVEL > LOG_LEVEL_DISABLED:
			func_name = _caller_name()
			current_time = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
			print(f"[{current_time}] [{log_level}] {func_name}() - {msg}", flush=True)


	def trace(msg: str):
		if LOG_LEVEL >= LOG_LEVEL_TRACE:
			Logging._log("TRACE", msg)


	def debug(msg: str):
		if LOG_LEVEL >= LOG_LEVEL_DEBUG:
			Logging._log("DEBUG", msg)


	def info(msg: str):
		if LOG_LEVEL >= LOG_LEVEL_INFO:
			Logging._log("INFO", msg)


	def warn(msg: str):
		if LOG_LEVEL >= LOG_LEVEL_WARN:
			Logging._log("WARN", msg)


	def error(msg: str):
		if LOG_LEVEL >= LOG_LEVEL_ERROR:
			Logging._log("ERROR", msg)



class Trace:

	def __enter__(self):
		if LOG_LEVEL > LOG_LEVEL_DISABLED:
			self.func_name = _caller_name(depth=3)
			print(f"[TRACE] {self.func_name}() - >")
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if LOG_LEVEL > LOG_LEVEL_DISABLED:
			print(f"[TRACE] {self.func_name}() - <")
		return False
