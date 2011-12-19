from lib import BeautifulSoup
from lib.utils import *
from log import *
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

class _document(object):
	def __init__(self, response, debug=False):
		self._response = response
		self._debugMode = debug
		self._url = u(self._response.getUrl())
		self._data = self._response.getData()
		self._soup = BeautifulSoup.BeautifulSoup(self._data)
		self._fakeResources = {}
		self._resources = []
	def _debug(self, *args):
		if self._debugMode:
			parserInfo(*args, force=True)
	def getUrl(self):
		return self._url
	def getResponse(self):
		return self._response
	def getData(self):
		return self._data
	def getSoup(self):
		return self._soup
	def resolveUrl(self, url):
		return urlparse.urljoin(self._url, u(url))
	def _getResourceRequest(self, resource):
		return httpRequest.httpRequest('GET', resource)
	def addResource(self, resource):
		if resource not in self._resources:
			self._resources.append(resource)
			self._debug('New resource detected:', resource)
			fetchy.backgroundCache(self._getResourceRequest(resource))
			return True
		return False
	def reserveResource(self, resource):
		if resource not in self._resources:
			self._resources.append(resource)
			self._debug('Resource reserved:', resource)
			return fetchy.reserveRequest(self._getResourceRequest(resource))
		return False
	def cancelResource(self, resource):
		if resource in self._resources:
			self._debug('Resource fetching cancelled:', resource)
			return fetchy.cancelRequest(self._getResourceRequest(resource))
	def cacheResource(self, resource, data, headers={}, responseCode=200):
		if resource in self._resources:
			self._debug('Resource cached:', resource)
			response = httpRequest.httpResponse(headers, data, finalUrl=resource, responseCode=responseCode)
			return fetchy.cacheResponse(cache.generateRequestKey(self._getResourceRequest(resource)), response)
	def streamResourceTo(self, resource, target, **kwargs):
		self._debug('Streaming resource', resource, 'to target', target)
		client.fetch(resource, toFeed=target, **kwargs)
	def registerFakeResource(self, key, callback):
		self._debug('Internal resource registered:', key)
		_fetchyResourceManager.add(key, callback)
	def getFakeResourceUrl(self, key):
		return u'http://fetchy/' + u(key)
	def __str__(self):
		return unicode(self).encode('utf8')
	def __unicode__(self):
		return mini.minify(unicode(self._soup))

def _processDocument(document, prettify=False):
	mini.process(document)
	if prettify:
		return document.getSoup().prettify()
	return unicode(document)

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

def testUrl(url):
	return _processDocument(_document(client.fetch(url), debug=True))
