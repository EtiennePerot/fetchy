from lib import BeautifulSoup
from lib.utils import *
import threading, urlparse
import client
import mini

class document(object):
	def __init__(self, response):
		self._response = response
		self._url = self._response.getUrl()
		self._data = self._response.getData()
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
			client.asyncFetch(resource) # Todo: Pass to cache
	def streamResourceTo(self, url, target):
		client.fetchToFunction(url, target)
	def registerFakeResource(self, key, callback):
		key = u(key)
		if key not in self._fakeResources:
			# Todo: Register key with global request handler
			self._fakeResources[key] = callback
	def getFakeResourceUrl(self, key):
		return u'http://fetchy/' + u(key)
	def __enter__(self):
		self._soupLock.acquire()
	def __exit__(self):
		self._soupLock.release()

def parse(url):
	doc = mini.process(document(client.fetch(url)))
	return doc.getSoup().prettify() # Temp: Do not prettify when not debugging. Prettifying is useful when debugging only.

#parse("http://stackoverflow.com/questions/1883980/find-the-nth-occurrence-of-substring-in-a-string")
print parse("http://www.crummy.com/software/BeautifulSoup/documentation.html")
