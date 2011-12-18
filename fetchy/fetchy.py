from lib.utils import *
from log import *
import threading
import mini
import cache
import parser
import client
import server

def _getResponse(request):
	if request.isFetchyInternal(): # Internal objects created by the parser
		response = parser.internalRequest(request)
	else: # Regular objects
		response = client.request(request)
		if response.isParsable():
			response = parser.processResponse(response)
	return response.toFetchyResponse(allowKeepAlive=request.isKeepAlive())

def cacheResponse(key, response):
	if key is not None and response is not None:
		cache.cacheResponse(key, response.toFetchyResponse())

def _backgroundCache(request):
	key = cache.generateRequestKey(request)
	response = _getResponse(request)
	if response is None:
		cache.cancel(key)
	else:
		cacheResponse(key, response)

def reserveRequest(request):
	cacheKey = cache.generateRequestKey(request)
	if cacheKey is not None:
		return cache.reserve(cacheKey)
	return False

def cancelRequest(request):
	cacheKey = cache.generateRequestKey(request)
	if cacheKey is not None:
		return cache.cancel(cacheKey)
	return False

def backgroundCache(request):
	if reserveRequest(request):
		threading.Thread(target=curry(_backgroundCache, request)).start()
	return True

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
	info('Starting with args', args, 'and kwargs', kwargs)
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
		return params
	from defaults import config as defaultConfig
	config = resolveConfig(config, defaultConfig)
	setLogVerbose(config['verbose'])
	setLogQuiet(config['quiet'])
	info('Final configuration:', config)
	mini.init(**config['mini'])
	cache.init(**config['cache'])
	client.init(**config['client'])
	server.init(**config['server'])

def getVersion():
	return u'0.1'
