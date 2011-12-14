from lib.utils import *
from log import *
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
			if k not in config:
				config[k] = defaultConfig[k]
			if type(defaultConfig[k]) is type({}):
				config[k] = resolveConfig(config[k], defaultConfig[k])
			elif type(config[k]) is not type(defaultConfig[k]):
				if type(config[k]) in (type(''), type(u'')) and type(defaultConfig[k]) in (type(''), type(u'')):
					config[k] = u(config[k])
				else:
					config[k] = defaultConfig[k]
	from defaults import config as defaultConfig
	config = resolveConfig(config, defaultConfig)
	setLogVerbose(config['verbose'])
	setLogQuiet(config['quiet'])
	info('Final configuration:', config)
	cache.init(config['cache']['gzipCompression'], config['cache']['diskCacheSize'], config['cache']['memoryCacheSize'], config['cache']['directory'])
	client.init(config['client']['bufferSize'], config['client']['httpTimeout'])
	server.init(config['server']['port'], config['server']['clientTimeout'], config['server']['bufferSize'])

def getVersion():
	return '0.1'
