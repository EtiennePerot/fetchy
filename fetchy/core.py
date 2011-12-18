from lib.utils import *
from log import *
import threading
import cachecontrol
import mini
import cache
import client
import server

def _getResponse(request):
	if request.isFetchyInternal(): # Internal objects created by the parser
		response = mini.internalRequest(request)
	else: # Regular objects
		response = client.request(request)
		if response is None:
			return None
		if response.isParsable():
			response = mini.processResponse(response)
	return response.toFetchyResponse(allowKeepAlive=request.isKeepAlive())

def handleRequest(request):
	cacheKey = cache.generateRequestKey(request)
	if cacheKey is not None:
		cachedResponse = cache.lookupResponse(cacheKey)
		if cachedResponse is not None:
			return cachedResponse
	response = _getResponse(request)
	cacheResponse(cacheKey, response)
	if response is not None and cacheKey is not None:
		return cache.lookupResponse(cacheKey)
	return response

def run(*args, **kwargs):
	mainInfo('Starting with args', args, 'and kwargs', kwargs)
	config = kwargs
	if len(args) and type(args[0]) is type({}):
		config = args[0]
	def resolveConfig(params, defaultParams):
		for k in defaultParams:
			if k not in params:
				params[k] = defaultParams[k]
			if type(defaultParams[k]) is type({}):
				params[k] = resolveConfig(params[k], defaultParams[k])
			elif type(params[k]) is not type(defaultParams[k]):
				if type(params[k]) in (type(''), type(u'')) and type(defaultParams[k]) in (type(''), type(u'')):
					params[k] = u(params[k])
				else:
					params[k] = defaultParams[k]
		for k in params:
			if k not in defaultParams:
				del params[k]
		return params
	from defaults import config as defaultConfig
	config = resolveConfig(config, defaultConfig)
	mainVerbose(config['verbose'])
	setLogQuiet(config['quiet'])
	mainInfo('Final configuration:', config)
	cachecontrol.init(_getResponse)
	mini.init(**config['mini'])
	cache.init(**config['cache'])
	client.init(**config['client'])
	server.init(**config['server'])

def getVersion():
	return u'0.1'
