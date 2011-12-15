from lib.utils import *
import urllib, urllib2, threading
import fetchy, httpHeaders
import zlib, gzip
from lib._StringIO import StringIO

class downloadResult:
	def __init__(self, data, finalUrl, status, headers):
		self._data = data
		self._finalUrl = finalUrl
		self._status = status
		self._contentType = headers.getContentType()
	def getData(self):
		return self._data
	def getFinalUrl(self):
		return self._finalUrl
	def getStatus(self):
		return self._status
	def getHeaders(self):
		return self._headers
	def getFullResponse(self):
		response = 'HTTP/1.1 ' + str(self._status) + '\r\n'
		response += 'Server: fetchy/' + fetchy.getVersion() + '\r\n'
		response += 'Connection: Keep-Alive\r\n'
		if self._contentType is not None:
			response += 'Content-Type: ' + self._contentType + '\r\n'
		if self._data is None:
			response += 'Content-Length: 0\r\n'
		else:
			response += 'Content-Length: ' + str(len(self._data)) + '\r\n'
			response += '\r\n' + self._data
		return response
	def __str__(self):
		return self._data
	def __unicode__(self):
		return u(self.data)

class _downloader(threading.Thread):
	_bufferSize = 16384
	_timeout = 10
	def __init__(self, url, headers=None, data=None, onSuccess=None, onFailure=None, toFeed=None):
		super(_downloader, self).__init__()
		self._url = url
		if headers is None:
			self._headers = httpHeaders.headers()
		else:
			self._headers = httpHeaders.headers(headers)
		self._headers['Accept-Encoding'] = 'gzip, deflate, identity'
		self._data = data
		self._onSuccess = onSuccess
		self._onFailure = onFailure
		self._toFeed = toFeed
	def _fail(self, errorCode=None):
		if self._onFailure is not None:
			self._onFailure(self, errorCode)
		if errorCode is None:
			return None
		return downloadResult(None, None, errorCode, httpHeaders.headers())
	def _getPostData(self):
		if self._data is None:
			return None
		s = []
		for key in self._data:
			s.append(urllib2.urlencode(u(key).encode('utf8')) + '=' + urllib2.urlencode(u(self._data[key]).encode('utf8')))
		return '&'.join(s)
	def _feed(self, data):
		if self._toFeed is not None:
			self._toFeed(data)
		return data
	def run(self):
		try:
			handle = urllib2.urlopen(urllib2.Request(self._url, self._getPostData(), self._headers.asDictionary()), timeout=_downloader._timeout)
		except urllib2.HTTPError, e:
			return self._fail(e.code)
		except:
			return self._fail()
		contents = ''
		contentEncoding = handle.info().get('Content-Encoding')
		if contentEncoding is not None and 'deflate' in contentEncoding:
			# Zlib mode; can only do it in one shot
			contents = self._feed(zlib.decompress(handle.read()))
		elif contentEncoding is not None and 'gzip' in contentEncoding:
			# Gzip mode; can only do it in one shot
			contents = self._feed(gzip.GzipFile(fileobj=StringIO(handle.read())).read())
		else:
			# Identity mode
			while True:
				try:
					data = handle.read(_downloader._bufferSize)
				except:
					break
				if not data:
					break
				contents += self._feed(data)
		result = downloadResult(contents, handle.geturl(), handle.getcode(), httpHeaders.headers(handle.info().headers))
		if self._onSuccess is not None:
			self._onSuccess(result)
		return result

def init(bufferSize, timeout):
	_downloader._bufferSize = bufferSize
	_downloader._timeout = timeout

def fetch(url, headers=None, data=None):
	return _downloader(url, headers=headers, data=data).run()

def asyncFetch(url, onSuccess=None, onFailure=None, headers=None, data=None):
	_downloader(url, headers=headers, data=data, onSuccess=onSuccess, onFailure=onFailure).start()

def fetchToFunction(url, toFeed, synchronous=True, headers=None, data=None):
	downloader = _downloader(url, headers=headers, data=data, toFeed=toFeed)
	if synchronous:
		downloader.run()
	else:
		downloader.start()
