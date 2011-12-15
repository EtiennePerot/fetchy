import os, gzip, tempfile, hashlib, urlparse, threading
from lib.utils import *
from log import *
from _StringIO import StringIO

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

class _cachedItem:
	def __init__(self, cacheableItem):
		self._key = cacheableItem.getKey()
		self._data = None
		self._size = None
	def getKey(self):
		return self._key
	def getSize(self):
		return self._size

class memoryCachedItem(_cachedItem):
	def __init__(self, cacheable):
		super(memoryCachedItem, self).__init__(cacheable)
		self._data = cacheable.getData()
		self._size = len(self._data)
	def toCacheable(self):
		return cacheableItem(self._key, self._data, knownSize=self._size)
	def getData(self):
		return self._data
	def writeTo(self, target):
		target.write(self._data)
		return self._size

class diskCachedItem(_cachedItem):
	_cacheDirectory = None
	def __init__(self, cacheable):
		super(diskCachedItem, self).__init__(cacheable)
		(scheme, netloc, path, params, query, fragment) = urlparse.urlparse(self._key, 'http')
		hash = u(hashlib.md5(self._key).hexdigest())
		if netloc:
			self._filename = os.path.join(diskCachedItem._cacheDirectory, u(netloc), hash + u'.cache')
		else:
			self._filename = os.path.join(diskCachedItem._cacheDirectory, u'unknown-domain', hash + u'.cache')
		dirname = os.path.dirname(self._filename)
		if not os.path.exists(dirname):
			os.makedirs(dirname)
		handle = open(self._filename, 'wb')
		self._size = cacheable.writeTo(handle)
		handle.close()
	def toCacheable(self):
		return cacheableItem(self._key, open(self._filename, 'rb'), knownSize=self._size, closeAfter=True)
	def getData(self):
		data = ''
		handle = open(self._filename, 'rb')
		i = handle.read(_bufferSize)
		while len(i):
			data += i
			i = handle.read(_bufferSize)
		handle.close()
		return data
	def writeTo(self, target):
		handle = open(self._filename, 'rb')
		i = handle.read(_bufferSize)
		while len(i):
			target.write(i)
			i = handle.read(_bufferSize)
		handle.close()
		return self._size

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
		self._lock.acquire()
		while self._availableSpace < size:
			self._prune()
		self._availableSpace -= size
		self.items[item.getKey()] = item
		self._orderedItems.append(item)
		self._lock.release()
	def lookup(self, key):
		if key in self._lookup:
			self._lock.acquire()
			item = self._lookup[key]
			self._orderedItems.remove(item)
			self._orderedItems.append(item)
			self._lock.release()
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
def init(gzipCompression, diskCacheSize, memoryCacheSize, cacheDirectory, bufferSize):
	global _bufferSize
	_bufferSize = bufferSize
	tempDir = u(tempfile.gettempdir())
	actualDirectory = u(cacheDirectory).replace(u'%tmp%', tempDir).encode()
	if not os.path.exists(actualDirectory):
		os.makedirs(actualDirectory)
	diskCachedItem._cacheDirectory = actualDirectory
	_fetchyCache = _cache(
		totalSize=memoryCacheSize,
		cachedClass=memoryCachedItem,
		acceptUnknownSize=False,
		levelBelow=_cache(
			totalSize=diskCacheSize,
			cachedClass=diskCachedItem
		)
	)
