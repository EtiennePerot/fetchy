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

class _littleLogger(object):
	def __init__(self, name):
		self._log = logging.getLogger(name)
		_allLogs.append(self)
	def log(self, level, *args, **kwargs):
		isForced = 'force' in kwargs and kwargs['force']
		if _logEnabled or isForced:
			if isForced:
				oldLevel = self._log.level
				self._log.setLevel(logging.DEBUG)
				del kwargs['force']
			self._log.log(level, _joinStr(args), **kwargs)
			if isForced:
				self._log.setLevel(oldLevel)
	def info(self, *args, **kwargs):
		self.log(logging.INFO, *args, **kwargs)
	def warn(self, *args, **kwargs):
		self.log(logging.WARN, *args, **kwargs)
	def error(self, *args, **kwargs):
		self.log(logging.ERROR, *args, **kwargs)
	def setLevel(self, level):
		self._log.setLevel(level)
	def setVerbose(self, verbose=None):
		oldLevel = self._log.level
		if verbose is not None:
			if verbose:
				self.setLevel(logging.INFO)
			else:
				self.setLevel(logging.WARN)
		return oldLevel

_mainLogger = _littleLogger('main')
mainLog = _mainLogger.log
mainInfo = _mainLogger.info
mainWarn = _mainLogger.warn
mainError = _mainLogger.error
mainVerbose = _mainLogger.setVerbose

_miniLogger = _littleLogger('mini')
miniLog = _miniLogger.log
miniInfo = _miniLogger.info
miniWarn = _miniLogger.warn
miniError = _miniLogger.error
miniVerbose = _miniLogger.setVerbose

_serverLogger = _littleLogger('server')
serverLog = _serverLogger.log
serverInfo = _serverLogger.info
serverWarn = _serverLogger.warn
serverError = _serverLogger.error
serverVerbose = _serverLogger.setVerbose

_clientLogger = _littleLogger('client')
clientLog = _clientLogger.log
clientInfo = _clientLogger.info
clientWarn = _clientLogger.warn
clientError = _clientLogger.error
clientVerbose = _clientLogger.setVerbose

_cacheLogger = _littleLogger('cache')
cacheLog = _cacheLogger.log
cacheInfo = _cacheLogger.info
cacheWarn = _cacheLogger.warn
cacheError = _cacheLogger.error
cacheVerbose = _cacheLogger.setVerbose

_parserLogger = _littleLogger('parser')
parserLog = _parserLogger.log
parserInfo = _parserLogger.info
parserWarn = _parserLogger.warn
parserError = _parserLogger.error
parserVerbose = _parserLogger.setVerbose

def setLogQuiet(quiet):
	global _logEnabled
	_logEnabled = not quiet
