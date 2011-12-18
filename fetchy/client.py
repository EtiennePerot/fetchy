from lib.utils import *
from log import *
import urllib, urllib2, urlparse, threading
import fetchy, httpRequest
import zlib, gzip
from lib._StringIO import StringIO

class _httpRedirectException(Exception):
	def __init__(self, req, fp, code, msg, hs):
		self._req = req
		self._fp = fp
		self._code = code
		self._msg = msg
		self._headers = httpRequest.headers(hs)
		if 'Location' in self._headers:
			self._location = self._headers['Location']
		elif 'uri' in self._headers:
			self._location = self._headers['uri']
		else:
			self._location = None
	def getFinalUrl(self):
		if self._location is None:
			return None
		urlparts = urlparse.urlparse(self._location)
		if not urlparts.path:
			urlparts = list(urlparts)
			urlparts[2] = '/'
		newurl = urlparse.urlunparse(urlparts)
		newurl = urlparse.urljoin(self._req.get_full_url(), newurl)
		return newurl

class _urlRedirectHandler(urllib2.HTTPRedirectHandler):
	def http_error_301(self, req, fp, code, msg, headers):
		raise _httpRedirectException(req, fp, code, msg, headers)
	http_error_302 = http_error_303 = http_error_307 = http_error_301

class _downloader(threading.Thread):
	_userAgent = 'fetchy'
	_bufferSize = 16384
	_timeout = 10
	_opener = urllib2.build_opener(_urlRedirectHandler)
	def __init__(self, url, headers=None, data=None, onSuccess=None, onFailure=None, toFeed=None):
		super(_downloader, self).__init__()
		self._url = url
		if headers is None:
			self._headers = httpRequest.headers()
		else:
			self._headers = httpRequest.headers(headers)
		self._headers['Accept-Encoding'] = 'gzip, deflate, identity'
		self._headers['Cache-Control'] = 'no-cache'
		self._headers['User-Agent'] = _downloader._userAgent
		del self._headers['Connection']
		del self._headers['if-modified-since']
		del self._headers['etag']
		del self._headers['Host']
		self._data = data
		self._onSuccess = onSuccess
		self._onFailure = onFailure
		self._toFeed = toFeed
	def _fail(self, errorCode=None):
		clientWarn('Client failed on', self._url, 'with error code', errorCode)
		if self._onFailure is not None:
			self._onFailure(self, errorCode)
		if errorCode is None:
			return None
		return httpRequest.httpResponse(None, None, responseCode=errorCode)
	def _getPostData(self):
		if self._data is None:
			return None
		if type(self._data) is type(u''):
			return self._data.encode('utf8')
		if type(self._data) is type(''):
			return self._data
		s = []
		for key in self._data:
			s.append(urllib2.urlencode(u(key).encode('utf8')) + '=' + urllib2.urlencode(u(self._data[key]).encode('utf8')))
		return '&'.join(s)
	def _feed(self, data):
		if self._toFeed is not None:
			try:
				self._toFeed(data)
			except:
				pass
		return data
	def run(self):
		clientInfo('Downloader running for', self._url)
		headersDict = self._headers.asDictionary()
		postData = self._getPostData()
		req = urllib2.Request(self._url, postData, headersDict)
		attempted = []
		successful = False
		while not successful:
			try:
				handle = _downloader._opener.open(req, timeout=_downloader._timeout)
			except _httpRedirectException, e:
				nextUrl = e.getFinalUrl()
				if nextUrl in attempted:
					clientWarn('Infinite redirect detected! Got redirected to', nextUrl, 'after attempts', attempted)
					return self._fail()
				clientInfo('Got redirect to', nextUrl, '- Current attempts:', attempted)
				attempted.append(nextUrl)
				req = urllib2.Request(nextUrl, postData, headersDict)
				continue
			except urllib2.HTTPError, e:
				return self._fail(e.code)
			except:
				return self._fail()
			successful = True
		contents = ''
		responseHeaders = httpRequest.headers(handle.info().headers)
		contentEncoding = responseHeaders['Content-Encoding']
		if contentEncoding is not None and 'deflate' in contentEncoding:
			# Zlib mode; can only do it in one shot
			contents = self._feed(zlib.decompress(handle.read()))
		elif contentEncoding is not None and 'gzip' in contentEncoding:
			# Gzip mode; can only do it in one shot due to lack of seek()/tell()
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
		result = httpRequest.httpResponse(responseHeaders, contents, responseCode=handle.getcode(), finalUrl=handle.geturl())
		if self._onSuccess is not None:
			try:
				self._onSuccess(result)
			except:
				pass
		clientInfo('Client successful for', self._url)
		return result

def init(verbose, userAgent, bufferSize, timeout):
	clientVerbose(verbose)
	_downloader._userAgent = userAgent
	_downloader._bufferSize = bufferSize
	_downloader._timeout = timeout

def request(request):
	return _downloader(request.getUrl(), request.getHeaders(), request.getData()).run()

def fetch(url, headers=None, data=None, toFeed=None, synchronous=True, onSuccess=None, onFailure=None):
	downloader = _downloader(url, headers=headers, data=data, toFeed=toFeed, onSuccess=onSuccess, onFailure=onFailure)
	if synchronous:
		return downloader.run()
	else:
		downloader.start()
