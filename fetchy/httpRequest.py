from lib.utils import *
from lib._StringIO import StringIO
import re, itertools, urlparse
import fetchy

_responseCodes = {
	100: u'Continue',
	101: u'Switching Protocols',
	200: u'OK',
	201: u'Created',
	202: u'Accepted',
	203: u'Non-Authoritative Information',
	204: u'No Content',
	205: u'Reset Content',
	206: u'Partial Content',
	300: u'Multiple Choices',
	301: u'Moved Permanently',
	302: u'Found',
	303: u'See Other',
	304: u'Not Modified',
	305: u'Use Proxy',
	307: u'Temporary Redirect',
	400: u'Bad Request',
	401: u'Unauthorized',
	402: u'Payment Required',
	403: u'Forbidden',
	404: u'Not Found',
	405: u'Method Not Allowed',
	406: u'Not Acceptable',
	407: u'Proxy Authorization Required',
	408: u'Request Timeout',
	409: u'Conflict',
	410: u'Gone',
	411: u'Length Required',
	412: u'Precondition Failed',
	413: u'Request Entity Too Large',
	414: u'Request-URI Too Long',
	415: u'Unsupported Media Type',
	416: u'Requested Range Not Satisfiable',
	417: u'Expectation Failed',
	500: u'Internal Server Error',
	501: u'Not Implemented',
	502: u'Bad Gateway',
	503: u'Service Unavailable',
	504: u'Gateway Timeout',
	505: u'HTTP Version Not Supported'
}

def _normalizeHeaderName(name):
	return u(name).strip().capitalize()

class _header(object):
	def __init__(self, *args):
		if len(args) == 2:
			self._header = _normalizeHeaderName(args[0])
			self._value = u(args[1]).strip()
		elif len(args) == 1:
			i = args[0].find(':')
			self._header = _normalizeHeaderName(args[0][:i])
			self._value = u(args[0][i + 1:]).strip()
		else:
			self._header = None
			self._value = None
		if self._header == u'proxy-connection':
			# Invalid header sadly used by all browsers
			# See http://homepage.ntlworld.com./jonathan.deboynepollard/FGA/web-proxy-connection-header.html
			self._header = u'connection'
	def writeTo(self, target):
		target(self.getHeader() + ': ' + self.getValue() + '\r\n')
		return len(self._header + self._value) + 4
	def getHeader(self):
		return self._header.encode('utf8')
	def getValue(self):
		return self._value.encode('utf8')
	def copy(self):
		return _header(self._header, self._value)
	def __str__(self):
		return u(self).encode('utf8')
	def __unicode__(self):
		if self._header is None:
			return u''
		return self._header + u': ' + self._value + u'\r\n'

class headers(object):
	_headerRegex = re.compile(u'^[-\\w]+\s*:')
	def __init__(self, *headers, **kwargs):
		if 'responseCode' in kwargs:
			self._responseCode = kwargs['responseCode']
		else:
			self._responseCode = None
		if 'httpVersion' in kwargs:
			self._httpVersion = u(kwargs['httpVersion'].strip())
		else:
			self._httpVersion = None
		if 'command' in kwargs:
			self._command = u(kwargs['command'].strip())
		else:
			self._command = None
		self._headers = []
		self.add(*headers)
	def add(self, *hs):
		for arg in hs:
			if arg is None:
				continue
			if type(arg) in (type(''), type(u'')):
				self._parseHeaders(u(arg))
			elif type(arg) in (type([]), type(())):
				self.add(*arg)
			elif isinstance(arg, _header):
				self._addHeader(arg)
			elif isinstance(arg, headers):
				for h in arg._headers:
					self._addHeader(h.copy())
				if arg._responseCode is not None:
					self._responseCode = arg._responseCode
				if arg._httpVersion is not None:
					self._httpVersion = arg._httpVersion
			else:
				for h in arg:
					self._addHeader(_header(h, arg[h]))
	def writeTo(self, target):
		size = 0
		if self._responseCode is not None:
			msg = ''
			if self._httpVersion is not None:
				msg += self._httpVersion.encode('utf8') + ' '
			msg += str(self._responseCode) + ' '
			if self._responseCode in _responseCodes:
				msg += _responseCodes[self._responseCode].encode('utf8')
			msg += '\r\n'
			size = len(msg)
			target(msg)
		for h in self._headers:
			size += h.writeTo(target)
		target('\r\n') # End headers
		return size + 2
	def getResponseCode(self):
		return self._responseCode
	def getHttpVersion(self):
		return self._httpVersion
	def getCommand(self):
		return self._command
	def get(self, header):
		header = _normalizeHeaderName(header)
		for h in self._headers:
			if h.getHeader() == header:
				return h.getValue()
		return None
	def delete(self, header):
		header = _normalizeHeaderName(header)
		for h in self._headers:
			if h.getHeader() == header:
				self._headers.remove(h)
				break
	def getContentType(self):
		contentType = self.get(u'content-type')
		if contentType is None:
			return None
		return contentType.lower()
	def isKeepAlive(self):
		headerVal = self.get(u'connection')
		if headerVal is not None:
			return headerVal.lower() == 'keep-alive'
		if self._httpVersion is None:
			return None # Unknown
		return self._httpVersion != u'HTTP/1.0' # False by default in HTTP/1.0, True by default in 1.1
	def asDictionary(self):
		d = {}
		for h in self._headers:
			d[h.getHeader()] = h.getValue()
		return d
	def setResponseCode(self, responseCode):
		self._responseCode = responseCode
	def setHttpVersion(self, version):
		self._httpVersion = u(version)
	def setCommand(self, command):
		self._command = u(version).strip().upper()
	def _parseHeaders(self, hs):
		hs = hs.split(u'\n')
		for h in hs:
			h = h.strip()
			if not len(h):
				continue
			if headers._headerRegex.search(h):
				self._addHeader(_header(h))
			else:
				s = h.split(u' ')
				if s[0][:5] == 'HTTP/':
					self._httpVersion = s[0].strip()
					try:
						self._responseCode = int(s[1].strip())
					except ValueError:
						pass
				elif s[-1][:5] == 'HTTP/':
					self._httpVersion = s[-1].strip()
					self._command = s[0].upper().strip()
	def _addHeader(self, header):
		self.delete(header.getHeader())
		self._headers.append(header)
	def __getitem__(self, key):
		return self.get(key)
	def __delitem__(self, key):
		self.delete(key)
	def __setitem__(self, key, value):
		if value is None:
			self.delete(key)
		else:
			self._addHeader(_header(key, value))
	def __iter__(self):
		return itertools.chain([x.getHeader() for x in self._headers])
	def __contains__(self, h):
		return self.get(h) is not None
	def __str__(self):
		return u(self).encode('utf8')
	def __unicode__(self):
		s = u''
		if self._httpVersion is not None and self._responseCode is not None:
			msg = u''
			if self._responseCode in _responseCodes:
				msg = _responseCodes[self._responseCode]
			s = self._httpVersion + u' ' + u(self._responseCode) + u' ' + msg + u'\r\n'
		for h in self._headers:
			s += u(h)
		return s + u'\r\n'

class httpMessage(object):
	def __init__(self, heads, data):
		self._data = data
		if not isinstance(heads, headers):
			heads = headers(heads)
		self._headers = heads
	def getData(self):
		return self._data
	def writeDataTo(self, target):
		pass
	def getHeaders(self):
		return self._headers
	def isKeepAlive(self):
		return self._headers.isKeepAlive()
	def getContentType(self):
		return self._headers.getContentType()
	def isParsable(self):
		contentType = self.getContentType()
		return contentType is not None and u'text/html' in contentType
	def __str__(self):
		return self._data
	def __unicode__(self):
		return u(self.data)

class httpRequest(httpMessage):
	def __init__(self, command, url, heads=None, data=None):
		super(httpRequest, self).__init__(heads, data)
		self._command = command
		self._url = url
	def getCommand(self):
		return self._command
	def getUrl(self):
		return self._url
	def isFetchyInternal(self):
		info = urlparse.urlparse(self._url, 'http')
		return info[1] and info[1] == 'fetchy'

class httpResponse(httpMessage):
	_fetchyPassthrough = ['Content-Encoding', 'Cookie', 'Etag', 'Date', 'Location'] # Todo: Pass more headers
	_chunkSize = 16384
	def __init__(self, heads, data, responseCode=None, finalUrl=None):
		super(httpResponse, self).__init__(heads, data)
		if responseCode is not None:
			self._headers.setResponseCode(responseCode)
		self._finalUrl = finalUrl
	def writeTo(self, target):
		data = self._data
		if type(data) is type(u''):
			data = data.encode('utf8')
		if type(data) is type(''):
			self._headers['Content-Length'] = len(data)
			data = StringIO(data)
		size = self._headers.writeTo(target)
		if data is not None:
			i = data.read(httpResponse._chunkSize)
			l = len(i)
			while l:
				chunk = hex(l)[2:]
				target(chunk + '\r\n' + i + '\r\n')
				size += l + len(chunk) + 4
				i = data.read(httpResponse._chunkSize)
				l = len(i)
		target('0\r\n') # Final chunk
		size += 3
		return size
	def getResponseCode(self):
		return self._headers.getResponseCode()
	def getUrl(self):
		return self._finalUrl
	def toFetchyResponse(self, allowKeepAlive=True):
		newHeaders = headers()
		newHeaders.setResponseCode(self._headers.getResponseCode())
		newHeaders.setHttpVersion('HTTP/1.1')
		newHeaders['X-Proxy-Server'] = 'fetchy/' + fetchy.getVersion()
		if allowKeepAlive:
			newHeaders['Connection'] = 'Keep-Alive'
		else:
			newHeaders['Connection'] = 'Close'
		newHeaders['Transfer-Encoding'] = 'chunked'
		for h in httpResponse._fetchyPassthrough:
			newHeaders[h] = self._headers[h]
		return httpResponse(newHeaders, self._data, responseCode=self._headers.getResponseCode(), finalUrl=self._finalUrl)

def init(chunkSize):
	httpResponse._chunkSize = chunkSize
