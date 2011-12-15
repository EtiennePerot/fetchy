import os, gzip, tempfile, base64, urlparse, threading
from lib.utils import *
from log import *
from lib._StringIO import StringIO

_bufferSize = 32768

class cacheableItem:
	def __init__(self, key, data, knownSize=None, closeAfter=False):
		self._key = key
		if type(data) is type(u''):
			self._data = data.encode('utf8')
		if type(data) is type(''):
			self._data = data
			self._isString = True
			self._closeAfter = False
			if knownSize is None:
				self._knownSize = len(self._data)
			else:
				self._knownSize = knownSize
		else:
			self._data = data
			self._isString = False
			self._closeAfter = closeAfter
			self._knownSize = knownSIze
	def getKnownSize(self):
		return self._knownSize
	def getKey(self):
		return self._key
	def getData(self):
		if self._isString:
			return self._data
		s = StringIO()
		i = self._data.read(_bufferSize)
		while len(i):
			s.write(i)
			i = self._data.read(_bufferSize)
		if self._closeAfter:
			self._data.close()
		return s.getvalue()
	def writeTo(self, target):
		if self._isString:
			target.write(self._data)
			return len(self._data)
		written = 0
		i = self._data.read(_bufferSize)
		while len(i):
			target.write(i)
			written += len(i)
			i = self._data.read(_bufferSize)
		if self._closeAfter:
			self._data.close()
		return written
	def discard(self):
		if self._closeAfter:
			self._data.close()
		self._data = None
		self._key = None

class cachedData:
	def __init__(self, gzipped, data):
		pass

class _cachedItem:
	gzipCompression = None
	gzipMinSize = None
	gzipMaxSize = None
	def __init__(self, cacheableItem):
		self._key = cacheableItem.getKey()
		self._data = None
		self._size = None
		self._gzipped = False
		self._gzipLock = threading.RLock()
	def _gzip(self):
		size = self.getSize()
		if size is not None and gzipMinSize <= size <= gzipMaxSize:
			threading.Thread(curry(self._backgroundGzip, _cachedItem.gzipCompression)).start()
	def getKey(self):
		return self._key
	def getSize(self):
		return self._size
	def toCacheable(self):
		pass
	def getData(self, gzipped=True):
		pass
	def writeTo(self, target, gzipped=True):
		pass
	def _backgroundGzip(self, compression):
		pass

class memoryCachedItem(_cachedItem):
	def __init__(self, cacheable):
		super(memoryCachedItem, self).__init__(cacheable)
		self._data = cacheable.getData()
		self._size = len(self._data)
		self._gzip()
	def toCacheable(self):
		return cacheableItem(self._key, self._data, knownSize=self._size)
	def getData(self):
		with self._gzipLock:
			return cachedData(self._gzipped, self._data)
	def writeTo(self, target):
		with self._gzipLock:
			target.write(self._data)
			return (self._gzipped, self._size)
	def _backgroundGzip(self, compression):
		gzippedData = gzip.GzipFile(fileobj=StringIO(self._data), compresslevel=compression).read()
		with self._gzipLock:
			self._data = gzippedData
			self._gzipped = True

class diskCachedItem(_cachedItem):
	_cacheDirectory = None
	_maxFilenameSize = 92
	def __init__(self, cacheable):
		super(diskCachedItem, self).__init__(cacheable)
		(scheme, netloc, path, params, query, fragment) = urlparse.urlparse(self._key, 'http')
		encodedPath = u(base64.urlsafe_b64encode(self._key))
		encodedPathComponents = []
		while len(encodedPath):
			i = min(diskCachedItem._maxFilenameSize, len(encodedPath))
			encodedPathComponents.append(encodedPath[:i])
			encodedPath = encodedPath[i:]
		if netloc:
			self._filename = os.path.join(diskCachedItem._cacheDirectory, u(netloc), *encodedPathComponents)
		else:
			self._filename = os.path.join(diskCachedItem._cacheDirectory, u'unknown-domain', *encodedPathComponents)
		dirname = os.path.dirname(self._filename)
		if not os.path.exists(dirname):
			os.makedirs(dirname)
		handle = open(self._properFilename(forceGzip=False), 'wb')
		self._size = cacheable.writeTo(handle)
		handle.close()
	def _properFilename(self, forceGzip=None):
		if (self._gzipped and forceGzip is not False) or forceGzip:
			return self._filename + u'.gz.cache'
		return self._filename + u'.raw.cache'
	def toCacheable(self):
		return cacheableItem(self._key, open(self._filename, 'rb'), knownSize=self._size, closeAfter=True)
	def getData(self):
		data = ''
		with self._gzipLock:
			handle = open(self._properFilename(), 'rb')
			i = handle.read(_bufferSize)
			while len(i):
				data += i
				i = handle.read(_bufferSize)
			handle.close()
			return cachedData(self._gzipped, data)
	def writeTo(self, target):
		with self._gzipLock:
			handle = open(self._properFilename(), 'rb')
			i = handle.read(_bufferSize)
			while len(i):
				target.write(i)
				i = handle.read(_bufferSize)
			handle.close()
			return (self._gzipped, self._size)
	def _backgroundGzip(self, compression):
		gzipHandle = gzip.GzipFile(filename=self._filename, mode='rb', compresslevel=compression)
		i = gzipHandle.read(_bufferSize)
		fHandle = open(self._properFilename(forceGzip=True), 'wb')
		while len(i):
			fHandle.write(i)
			i = gzipHandle.read(_bufferSize)
		fHandle.close()
		gzipHandle.close()
		with self._gzipLock:
			self._gzipped = True
			os.remove(path)

class _cache:
	def __init__(self, totalSize, cachedClass, acceptUnknownSize=True, levelBelow=None):
		self._totalSize = totalSize
		self._availableSpace = totalSize
		self._levelBelow = levelBelow
		self._cachedClass = cachedClass
		self._acceptUnknownSize = acceptUnknownSize
		self._items = {}
		self._orderedItems = []
		self._lock = threading.RLock()
	def add(self, item):
		size = item.getKnownSize()
		if (size is None and not self._acceptUnknownSize) or size > self._totalSize:
			# Too big to fit, or unacceptable
			if self._levelBelow is not None: # Forward it down
				self._levelBelow.add(item)
			return
		item = self._cachedClass(item)
		size = item.getSize()
		with self._lock:
			while self._availableSpace < size:
				self._prune()
			self._availableSpace -= size
			self.items[item.getKey()] = item
			self._orderedItems.append(item)
	def lookup(self, key):
		if key in self._lookup:
			with self._lock:
				item = self._lookup[key]
				self._orderedItems.remove(item)
				self._orderedItems.append(item)
			return item
		if self._levelBelow is not None: # Forward it down
			return self._levelBelow.lookup(key)
		return None
	def _prune(self):
		toPrune = self._orderedItems.pop(0)
		del self._items[toPrune.getKey()]
		self._availableSpace += toPrune.getSize()
		if self._levelBelow is not None: # Forward it down
			self._levelBelow.add(toPrune.toCacheable())

_fetchyCache = None
def init(gzipCompression, gzipMinSize, gzipMaxSize, diskCacheSize, memoryCacheSize, directory, bufferSize):
	global _bufferSize
	_bufferSize = bufferSize
	tempDir = u(tempfile.gettempdir())
	actualDirectory = u(directory).replace(u'%tmp%', tempDir).encode()
	if not os.path.exists(actualDirectory):
		os.makedirs(actualDirectory)
	diskCachedItem._cacheDirectory = actualDirectory
	_cachedItem.gzipCompression = gzipCompression
	_cachedItem.gzipMinSize = gzipMinSize
	_cachedItem.gzipMaxSize = gzipMaxSize
	_fetchyCache = _cache(
		totalSize=memoryCacheSize,
		cachedClass=memoryCachedItem,
		acceptUnknownSize=False,
		levelBelow=_cache(
			totalSize=diskCacheSize,
			cachedClass=diskCachedItem
		)
	)
