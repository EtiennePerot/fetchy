#!/usr/bin/env python

import sys, fetchy.parser
from fetchy.lib.utils import *

args = sys.argv[1:]
if not len(args):
	print >> sys.stderr, 'Usage: fetchy-parser-test.py \'URL1\' \'URL2\' \'URL3\' ...'
	print >> sys.stderr, 'You must provide at least one URL as argument.'
	sys.exit(1)
for url in args:
	print >> sys.stderr, 'Processing URL:', url
	try:
		data = u(fetchy.parser.testUrl(url))
		try:
			print data
		except:
			try:
				print data.encode('utf8')
			except:
				pass
	except Exception, e:
		print >> sys.stderr, 'Error while processing URL:', url
		print >> sys.stderr, 'Error was:', e
