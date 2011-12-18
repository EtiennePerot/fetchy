import css, js, images
import html, urlparse, threading, re
from ..lib import slimmer, BeautifulSoup
from ..lib.utils import *
from ..log import *
from .. import cachecontrol
from .. import client
from .. import cache
from .. import httpRequest

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
	def __init__(self, url, data):
		self._url = u(url)
		self._data = u(data)
		self._soup = BeautifulSoup.BeautifulSoup(self._data)
		self._fakeResources = {}
		self._resources = []
	def getUrl(self):
		return self._url
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
			cachecontrol.backgroundCache(self._getResourceRequest(resource))
			return True
		return False
	def reserveResource(self, resource):
		if resource not in self._resources:
			self._resources.append(resource)
			return core.reserveRequest(self._getResourceRequest(resource))
		return False
	def cancelResource(self, resource):
		if resource in self._resources:
			return cachecontrol.cancelRequest(self._getResourceRequest(resource))
		return False
	def cacheResource(self, resource, data, headers={}, responseCode=200):
		if resource in self._resources:
			response = httpRequest.httpResponse(headers, data, finalUrl=resource, responseCode=responseCode)
			return cachecontrol.cacheResponse(cache.generateRequestKey(self._getResourceRequest(resource)), response)
		return False
	def streamResourceTo(self, resource, target, **kwargs):
		client.fetch(resource, toFeed=target, **kwargs)
	def registerFakeResource(self, key, callback):
		_fetchyResourceManager.add(key, callback)
	def getFakeResourceUrl(self, key):
		return u'http://fetchy/' + u(key)

def _process(document, prettify=False):
	js.process(document)
	css.process(document)
	images.process(document)
	for comment in document.getSoup().findAll(lambda x : isinstance(x, BeautifulSoup.Comment)):
		comment.extract()
	finalSoup = document.getSoup()
	if prettify:
		return finalSoup.prettify()
	return unicode(finalSoup)

_enabled = True
_hardcore = True

def _minimizeHtml(html):
	if not _enabled:
		return html
	return slimmer.slimmer(html, hardcore=_hardcore)

def processResponse(response):
	html = _process(_document(response.getUrl(), _minimizeHtml(response.getData())))
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
	return processResponse(client.fetch(url))

def init(**kwargs):
	global _enabled, _hardcore
	_enabled = kwargs['html']['enabled']
	_hardcore = kwargs['html']['hardcore']
	miniVerbose(kwargs['verbose'])
	js.init(**kwargs['js'])
	css.init(**kwargs['css'])
	images.init(**kwargs['images'])
