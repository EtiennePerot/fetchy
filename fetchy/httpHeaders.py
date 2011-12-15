from lib.utils import *
import itertools

class _header:
	def __init__(self, *args):
		if len(args) == 2:
			self._header = u(args[0]).lower().strip()
			self._value = u(args[1]).strip()
		elif len(args) == 1:
			i = args[0].find(':')
			self._header = u(args[0][:i]).lower().strip()
			self._value = u(args[0][i + 1:]).strip()
		else:
			self._header = None
			self._value = None
		if self._header == u'proxy-connection':
			# Invalid header sadly used by all browsers
			# See http://homepage.ntlworld.com./jonathan.deboynepollard/FGA/web-proxy-connection-header.html
			self._header = u'connection'
	def getHeader(self):
		return self._header.encode('utf8')
	def getValue(self):
		return self._value.encode('utf8')
	def copy(self):
		return _header(self._header, self._value)
	def __str__(self):
		return u(self).encode('utf8')
	def __unicode(self):
		if self._header is None:
			return u''
		return self._header + u': ' + self._value

class headers:
	def __init__(self, *headers, **kwargs):
		if 'responseCode' in kwargs:
			self._responseCode = kwargs['responseCode']
		else:
			self._responseCode = None
		if 'httpVersion' in kwargs:
			self._httpVersion = u(kwargs['httpVersion'].strip())
		else:
			self._httpVersion = None
		self._headers = []
		self.add(*headers)
	def add(self, *hs):
		for arg in hs:
			if type(arg) in (type(''), type(u'')):
				self._parseHeaders(u(arg))
			elif type(arg) in (type([]), type(())):
				self.add(*arg)
			elif isinstance(arg, _header):
				self._addHeader(arg)
			elif isinstance(arg, headers):
				for h in arg._headers:
					self._addHeader(h.copy())
			else:
				for h in arg:
					self._addHeader(_header(h, arg[h]))
	def getResponseCode(self):
		return self._responseCode
	def getHttpVersion(self):
		return self._httpVersion
	def get(self, header):
		header = u(header).lower().strip()
		for h in self._headers:
			if h.getHeader() == header:
				return h.getValue()
		return None
	def delete(self, header):
		header = u(header).lower().strip()
		for h in self._headers:
			if h.getHeader() == header:
				self._headers.remove(h)
				break
	def getContentType(self):
		return self.get(u'content-type')
	def isKeepAlive(self):
		headerVal = self.get(u'connection')
		if headerVal is not None:
			return headerVal.lower() == 'keep-alive'
		if self._httpVersion is None:
			return None # Unknown
		return self._httpVersion != 'HTTP/1.0' # False by default in HTTP/1.0, True by default in 1.1
	def asDictionary(self):
		d = {}
		for h in self._headers:
			d[h.getHeader()] = h.getValue()
		return d
	def _parseHeaders(self, headers):
		headers = headers.split(u'\n')
		for h in headers:
			if h.find(':') != -1:
				self._addHeader(_header(h))
			elif h[:5] == 'HTTP/':
				s = h.split(u' ')
				self._httpVersion = s[0].strip()
				try:
					self._responseCode = int(s[1].strip())
				except ValueError:
					pass
	def _addHeader(self, header):
		self.delete(header.getHeader())
		self._headers.append(header)
	def __getitem__(self, key):
		return self.get(key)
	def __delitem__(self, key):
		self.delete(key)
	def __setitem__(self, key, value):
		self._addHeader(_header(key, value))
	def __iter__(self):
		return itertools.chain([x.getHeader() for x in self._headers])
	def __str__(self):
		return u(self).encode('utf8')
	def __unicode__(self):
		s = u''
		for h in self._headers:
			s += u(h)
		return s
