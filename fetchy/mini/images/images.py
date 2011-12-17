import bmp, jpeg, png, tga
import urlparse
from ...lib.utils import *

def processImage(document, url):
	(scheme, netloc, path, params, query, fragment) = urlparse.urlparse(u(url), 'http')
	dot = path.find(u'.')
	if dot != -1:
		extension = path[dot + 1:].lower().strip()
		if extension == u'png':
			png.process(document, url)
			return True
		if extension in (u'jpg', u'jpeg'):
			jpeg.process(document, url)
			return True
		if extension == u'bmp':
			bmp.process(document, url)
			return True
		if extension == u'tga':
			tga.process(document, url)
			return True
	return False

def process(document):
	soup = document.getSoup()
	images = soup('img')
	for image in images:
		try:
			url = document.resolveUrl(image['src'])
			if not processImage(document, url):
				document.addResource(url)
		except KeyError:
			continue

def init(**kwargs):
	png.init(**kwargs['png'])
	jpeg.init(**kwargs['jpeg'])
	bmp.init(**kwargs['bmp'])
	tga.init(**kwargs['tga'])
