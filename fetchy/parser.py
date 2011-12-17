from lib import BeautifulSoup
from lib.utils import *
import threading, re, urlparse
import fetchy
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

class _document(object):
	_removeHtmlJunk = re.compile(u'^\\s*<!DOCTYPE[^<>]*>\\s*|<!--(?:(?!-->).)*-->', re.IGNORECASE | re.DOTALL)
	def __init__(self, response):
		self._response = response
		self._url = self._response.getUrl()
		self._data = _document._removeHtmlJunk.sub(u'', self._response.getData())
		self._soup = BeautifulSoup.BeautifulSoup(self._data)
		self._fakeResources = {}
		self._resources = []
	def getUrl(self):
		return self._url
	def getResponse(self):
		return self._response
	def getData(self):
		return self._data
	def getSoup(self):
		return self._soup
	def resolveUrl(self, url):
		return urlparse.urljoin(self._url, url)
	def addResource(self, resource):
		if resource not in self._resources:
			self._resources.append(resource)
			fetchy.backgroundCache(httpRequest.httpRequest('GET', resource))
	def streamResourceTo(self, url, target):
		client.fetchToFunction(url, target)
	def registerFakeResource(self, key, callback):
		_fetchyResourceManager.add(key, callback)
	def getFakeResourceUrl(self, key):
		return u'http://fetchy/' + u(key)
	def __enter__(self):
		self._soupLock.acquire()
	def __exit__(self):
		self._soupLock.release()

def _processDocument(document, prettyify=False):
	mini.process(document)
	finalSoup = document.getSoup()
	if prettyify:
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
	return _processDocument(_document(client.fetch(url)))
