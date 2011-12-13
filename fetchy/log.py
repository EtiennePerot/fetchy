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

_mainLog = logging.getLogger('fetchy')
def log(level, *args, **kwargs):
	if _logEnabled:
		_mainLog.log(level, _joinStr(args), **kwargs)
def info(*args, **kwargs):
	log(logging.INFO, *args, **kwargs)
def warn(*args, **kwargs):
	log(logging.WARN, *args, **kwargs)
def error(*args, **kwargs):
	log(logging.ERROR, *args, **kwargs)
_allLogs.append(_mainLog)

_serverLog = logging.getLogger('server')
def serverLog(level, *args, **kwargs):
	if _logEnabled:
		_serverLog.log(level, _joinStr(args), **kwargs)
def serverInfo(*args, **kwargs):
	serverLog(logging.INFO, *args, **kwargs)
def serverWarn(*args, **kwargs):
	serverLog(logging.WARN, *args, **kwargs)
def serverError(*args, **kwargs):
	serverLog(logging.ERROR, *args, **kwargs)
_allLogs.append(_serverLog)

_clientLog = logging.getLogger('client')
def clientLog(level, *args, **kwargs):
	if _logEnabled:
		_clientLog.log(level, _joinStr(args), **kwargs)
def clientInfo(*args, **kwargs):
	clientLog(logging.INFO, *args, **kwargs)
def clientWarn(*args, **kwargs):
	clientLog(logging.WARN, *args, **kwargs)
def clientError(*args, **kwargs):
	clientLog(logging.ERROR, *args, **kwargs)
_allLogs.append(_clientLog)

def setLogVerbose(verbose):
	level = logging.WARN
	if verbose:
		level = logging.INFO
	for l in _allLogs:
		l.setLevel(level)

def setLogQuiet(quiet):
	global _logEnabled
	_logEnabled = not quiet
