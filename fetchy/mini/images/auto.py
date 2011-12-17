import bmp, jpeg, png, tga
import urlparse

def auto(image):
	pass # Todo: Detect format, pass to appropriate module

def process(document):
	soup = document.getSoup()
	url = document.getUrl()
	images = soup('img')
	for image in images:
		try:
			src = image['src']
			url = urlparse.urljoin(url, src)
			document.addResource(url)
		except KeyError:
			continue

	#TODO put in cache, jpegtran, pngcrush, transform bmp and tga images
