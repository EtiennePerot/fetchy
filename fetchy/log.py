import logging
from lib.utils import *

_allLogs = []
_logEnabled = True

logging.basicConfig()

def _joinStr(args):
	s = []
	for i in args:
		s.append(u(i))
	return u' '.join(s).strip()

class _littleLogger:
	def __init__(self, name):
		self._log = logging.getLogger(name)
		_allLogs.append(self)
	def log(self, level, *args, **kwargs):
		if _logEnabled:
			self._log.log(level, _joinStr(args), **kwargs)
	def info(self, *args, **kwargs):
		self.log(logging.INFO, *args, **kwargs)
	def warn(self, *args, **kwargs):
		self.log(logging.WARN, *args, **kwargs)
	def error(self, *args, **kwargs):
		self.log(logging.ERROR, *args, **kwargs)
	def setLevel(self, level):
		self._log.setLevel(level)

_mainLogger = _littleLogger('main')
log = _mainLogger.log
info = _mainLogger.info
warn = _mainLogger.warn
error = _mainLogger.error

_serverLogger = _littleLogger('server')
serverLog = _serverLogger.log
serverInfo = _serverLogger.info
serverWarn = _serverLogger.warn
serverError = _serverLogger.error

_clientLogger = _littleLogger('client')
clientLog = _clientLogger.log
clientInfo = _clientLogger.info
clientWarn = _clientLogger.warn
clientError = _clientLogger.error

_cacheLogger = _littleLogger('cache')
cacheLog = _cacheLogger.log
cacheInfo = _cacheLogger.info
cacheWarn = _cacheLogger.warn
cacheError = _cacheLogger.error

def setLogVerbose(verbose):
	level = logging.WARN
	if verbose:
		level = logging.INFO
	for l in _allLogs:
		l.setLevel(level)

def setLogQuiet(quiet):
	global _logEnabled
	_logEnabled = not quiet
