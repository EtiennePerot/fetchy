import os, gzip, time, tempfile, hashlib, urlparse
from lib.utils import *
from log import *
from _StringIO import StringIO

_bufferSize = 32768

class cacheableItem:
	def __init__(self, key, data):
		self._key = key
		if type(data) is type(u''):
			self._data = data.encode('utf8')
		if type(data) is type(''):
			self._data = data
			self._isString = True
		else:
			self._data = data
			self._isString = False
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
		return s.getvalue()
	def writeTo(self, target):
		if self._isString:
			target.write(self._data)
		else:
			i = self._data.read(_bufferSize)
			while len(i):
				target.write(i)
				i = self._data.read(_bufferSize)

class _cachedItem:
	def __init__(self, cacheableItem):
		self._key = cacheableItem.getKey()
		self._data = None
		self._size = None
		self._lastAccess = time.time()
	def getKey(self):
		return self._key
	def getSize(self):
		return self._size
	def getLastAccess(self):
		return self._lastAccess
	def touch(self):
		self._lastAccess = time.time()
	def __cmp__(self, other):
		if other is None:
			return 9001
		return self._lastAccess - other._lastAccess

def memoryCachedItem(_cachedItem):
	def __init__(self, cacheable):
		super(memoryCachedItem, self).__init__(cacheable)
		self._data = cacheable.getData()
		self._size = len(self._data)

def diskCachedItem(_cachedItem):
	_cacheDirectory = None
	def __init__(self, cacheable):
		super(diskCachedItem, self).__init__(cacheable)
		(scheme, netloc, path, params, query, fragment) = urlparse.urlparse(self._key, 'http')
		hash = u(hashlib.md5(self._key).hexdigest())
		if netloc:
			filename = os.path.join(diskCachedItem._cacheDirectory, u(netloc), hash + u'.cache')
		else:
			filename = os.path.join(diskCachedItem._cacheDirectory, u'unknown-domain', hash + u'.cache')
		handle = open(filename, 'wb')
		cacheable.writeTo(handle)
		self._size = os.path.getsize(filename)

class _cacheLevel:
	def __init__(self, totalSize, levelBelow=None):
		self._totalSize = totalSize
		self._availableSpace = totalSize
		self._levelBelow = levelBelow
		self._items = {}
	def add(self, item):
		size = item.getSize()
		if size > self._totalSize:
			# Too big to fit at all
			if self._levelBelow is not None: # Forward it down
				self._levelBelow.add(item)
			return
		while self._availableSpace < size:
			self._prune()
		self._availableSpace -= size
		self.items[item.getKey()] = item
	def lookup(self, key):
		if key in self._lookup:
			item = self._lookup[key]
			item.touch()
			return item
		if self._levelBelow is not None: # Forward it down
			return self._levelBelow.lookup(key)
		return None
	def _prune(self):
		lowestAccess = time.time() + 1 # It's from the future!
		lowestItem = None
		for item in self._items.values():
			access = item.getLastAccess()
			if access < lowestAccess:
				lowestAccess = access
				lowestItem = item
		del self._items[lowestItem.getKey()]
		self._availableSpace += lowestItem.getSize()
		if self._levelBelow is not None: # Forward it down
			self._levelBelow.add(lowestItem)

class _cache:
	def __init__(self, levels):
		self._levels = levels
	def add(self, item):
		self._levels[0].add(item)
	def lookup(self, key):
		return self._levels[0].lookup(key)

_fetchyCache = None
def init(gzipCompression, diskCacheSize, memoryCacheSize, cacheDirectory, bufferSize):
	global _bufferSize
	_bufferSize = bufferSize
	tempDir = u(tempfile.gettempdir())
	actualDirectory = u(cacheDirectory).replace(u'%tmp%', tempDir).encode()
	if not os.path.exists(actualDirectory):
		os.makedirs(actualDirectory)
	if actualDirectory[-1] != u(os.sep):
		actualDirectory += u(os.sep)
	diskCachedItem._cacheDirectory = actualDirectory
	_fetchyCache = _cache(gzipCompression, diskCacheSize, memoryCacheSize, cacheDirectory)
