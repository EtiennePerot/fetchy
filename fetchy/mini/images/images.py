import bmp, jpeg, png, tga
import urlparse
from ...lib.utils import *

def processImage(document, url):
	(scheme, netloc, path, params, query, fragment) = urlparse.urlparse(u(url), 'http')
	dot = path.find(u'.')
	if dot != -1:
		extension = path[dot + 1:].lower().strip()
		if extension == u'png':
			return png.process(document, url)
		if extension in (u'jpg', u'jpeg'):
			return jpeg.process(document, url)
		if extension == u'bmp':
			return bmp.process(document, url)
		if extension == u'tga':
			return tga.process(document, url)
	return False

def process(document):
	soup = document.getSoup()
	images = soup('img')
	for image in images:
		try:
			url = document.resolveUrl(image['src'])
			func = processImage(document, url)
			if func:
				document.reserveResource(url)
				func()
			else:
				document.addResource(url)
		except KeyError:
			continue

def init(**kwargs):
	png.init(**kwargs['png'])
	jpeg.init(**kwargs['jpeg'])
	bmp.init(**kwargs['bmp'])
	tga.init(**kwargs['tga'])
