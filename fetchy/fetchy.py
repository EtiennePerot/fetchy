from lib.utils import *
from log import *
import server

def run(*args, **kwargs):
	info('Starting with args', args, 'and kwargs', kwargs)
	config = kwargs
	if len(args) and type(args[0]) is type({}):
		config = args[0]
	from defaults import config as defaultConfig
	for k in defaultConfig:
		if k not in config:
			config[k] = defaultConfig[k]
		elif type(config[k]) is not type(defaultConfig[k]):
			if type(config[k]) in (type(''), type(u'')) and type(defaultConfig[k]) in (type(''), type(u'')):
				config[k] = u(config[k])
			else:
				config[k] = defaultConfig[k]
	setLogVerbose(config['verbose'])
	setLogQuiet(config['quiet'])
	info('Final configuration:', config)
	server.run(config['port'])
