from lib import BeautifulSoup
import threading
import client
import mini

class document(object):
	def __init__(self, response):
		self._response = response
		self._url = self._response.getUrl()
		self._data = self._response.getData()
		self._soup = BeautifulSoup.BeautifulSoup(self._data)
		self._resourceLock = threading.RLock()
		self._resources = []
	def getUrl(self):
		return self._url
	def getResponse(self):
		return self._response
	def getData(self):
		return self._data
	def getSoup(self):
		return self._soup
	def addResource(self, resource):
		with self._resourceLock:
			if resource not in self._resources:
				self._resources.append(resource)
				client.asyncFetch(resource) # Todo: Pass to cache

def parse(url):
	return mini.process(document(client.fetch(url)))

#parse("http://stackoverflow.com/questions/1883980/find-the-nth-occurrence-of-substring-in-a-string")
parse("http://www.crummy.com/software/BeautifulSoup/documentation.html")
