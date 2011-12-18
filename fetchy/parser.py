from lib import BeautifulSoup
from lib.utils import *
import threading, re, urlparse
import fetchy
import cache
import client
import mini
import httpRequest

class _resourceManager(object):
	def __init__(self):
		self._resources = {}
		self._lock = threading.RLock()
	def add(self, key, callback):
		key = u(key)
		with self._lock:
			self._resources[key] = callback
	def get(self, key):
		key = u(key)
		with self._lock:
			if key in self._resources:
				val = self._resources[key]
				del self._resources[key]
				return val
		return None
_fetchyResourceManager = _resourceManager()

def _processDocument(document, prettify=False):
	mini.process(document)
	finalSoup = document.getSoup()
	if prettify:
		return finalSoup.prettify()
	return unicode(finalSoup)

def processResponse(response):
	html = _processDocument(_document(response))
	return httpRequest.httpResponse(response.getHeaders(), html)

def internalRequest(request):
	reqUrl = request.getUrl()
	(scheme, netloc, path, params, query, fragment) = urlparse.urlparse(reqUrl, 'http')
	key = path[1:]
	data = _fetchyResourceManager.get(key)
	if data is None:
		return None
	return data(key, reqUrl)

def tempTest(url): # Todo: Remove me
	return _processDocument(mini._document(client.fetch(url)))
