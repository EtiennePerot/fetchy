from lib.utils import *
from log import *
import cache
import client
import server

def handleRequest(url, headers, data=None):
	response = client.fetch(url, headers=headers, data=data)
	if response is None:
		return None
	else:
		return response.getFullResponse()

def run(*args, **kwargs):
	info('Starting with args', args, 'and kwargs', kwargs)
	config = kwargs
	if len(args) and type(args[0]) is type({}):
		config = args[0]
	def resolveConfig(params, defaultParams):
		for k in defaultParams:
			print 'Runnin', k, defaultParams
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
	cache.init(**config['cache'])
	client.init(**config['client'])
	server.init(**config['server'])

def getVersion():
	return '0.1'
