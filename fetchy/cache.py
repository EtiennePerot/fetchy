import os, gzip, tempfile, base64, threading
from lib.utils import *
from log import *
import httpRequest
from lib._StringIO import StringIO

_bufferSize = 32768

class _streamableData(object):
	def __init__(self, data, knownSize=None, closeAfter=None):
		self._data = data
		self._knownSize = knownSize
		if type(self._data) is type(u''):
			self._data = self._data.encode('utf8')
		if type(self._data) is type(''):
			self._isString = True
			self._closeAfter = False
			if self._knownSize is None:
				self._knownSize = len(self._data)
		else:
			self._isString = False
			self._closeAfter = closeAfter
	def getKnownSize(self):
		return self._knownSize
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
		if self._data is None:
			cacheWarn('Attempted to write the same cache data twice.')
			return
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
		self._data = None
		return written
	def discard(self):
		if self._closeAfter:
			self._data.close()
		self._data = None

class _cacheableItem(object):
	def __init__(self, key, pristine, compressible):
		self._key = key
		self._pristine = pristine
		if self._pristine is None:
			self._pristine = ''
		if not isinstance(self._pristine, _streamableData):
			self._pristine = _streamableData(self._pristine)
		self._compressible = compressible
		if self._compressible is None:
			self._compressible = ''
		if not isinstance(self._compressible, _streamableData):
			self._compressible = _streamableData(self._compressible)
	def getKey(self):
		return self._key
	def getPristineKnownSize(self):
		return self._pristine.getKnownSize()
	def getPristineData(self):
		return self._pristine.getData()
	def writePristineTo(self, target):
		return self._pristine.writeTo(target)
	def discardPristine(self):
		return self._pristine.discard
	def getCompressibleKnownSize(self):
		return self._compressible.getKnownSize()
	def getCompressibleData(self):
		return self._compressible.getData()
	def writeCompressibleTo(self, target):
		return self._compressible.writeTo(target)
	def discardCompressible(self):
		return self._compressible.discard
	def getKnownSize(self):
		pristineSize = self.getPristineKnownSize()
		compressibleSize = self.getCompressibleKnownSize()
		if pristineSize is None or compressibleSize is None:
			return None
		return pristineSize + compressibleSize

class _gzippedData(_streamableData):
	def __init__(self, gzipped, data, knownSize, closeAfter=True):
		super(_gzippedData, self).__init__(data, knownSize=knownSize, closeAfter=closeAfter)
		self._gzipped = gzipped
	def isGzipped(self):
		return self._gzipped
	def getContentEncoding(self):
		if self._gzipped:
			return 'gzip'
		return 'identity'

class _cachedItem(object):
	gzipCompression = None
	gzipMinSize = None
	gzipMaxSize = None
	def __init__(self, cacheableItem):
		self._key = cacheableItem.getKey()
		self._size = None
		self._pristineSize = None
		self._compressibleSize = None
		self._gzipped = False
		self._gzipLock = threading.RLock()
		self._gzipDone = threading.Condition(self._gzipLock)
	def _finalize(self):
		if self._pristineSize is not None and self._compressibleSize is not None:
			self._size = self._pristineSize + self._compressibleSize
		self._compressedSize = self._compressibleSize
		if self._size is not None and _cachedItem.gzipMinSize <= self._size <= _cachedItem.gzipMaxSize:
			threading.Thread(target=curry(self._gzipMonitor, _cachedItem.gzipCompression)).start()
	def _waitForGzip(self, waitForGzip=True):
		if waitForGzip:
			with self._gzipLock:
				while not self._gzipped:
					self._gzipDone.wait()
	def getKey(self):
		return self._key
	def getSize(self):
		return self._size
	def toCacheable(self):
		pass
	def getPristineData(self):
		pass
	def writePristineTo(self, target):
		pass
	def getCompressibleData(self, gzipped=True):
		pass
	def writeCompressibleTo(self, target, gzipped=True):
		pass
	def _gzipMonitor(self, compression):
		self._backgroundGzip(compression)
		with self._gzipLock:
			self._gzipDone.notifyAll()
	def _backgroundGzip(self, compression):
		pass

class memoryCachedItem(_cachedItem):
	def __init__(self, cacheable):
		super(memoryCachedItem, self).__init__(cacheable)
		self._pristine = cacheable.getPristineData()
		self._compressible = cacheable.getCompressibleData()
		self._pristineSize = len(self._pristine)
		self._compressibleSize = len(self._compressible)
		self._finalize()
	def toCacheable(self):
		return _cacheableItem(self._key, _streamableData(self._pristine), _streamableData(self._compressible))
	def getPristineData(self):
		return self._pristine
	def writePristineTo(self, target):
		target.write(self._pristine)
		return self._pristineSize
	def getCompressibleData(self, waitForGzip=False):
		self._waitForGzip(waitForGzip)
		with self._gzipLock:
			return _gzippedData(self._gzipped, self._compressible, self._compressedSize)
	def writeCompressibleTo(self, target, waitForGzip=False):
		self._waitForGzip(waitForGzip)
		with self._gzipLock:
			target.write(self._data)
			return (self._gzipped, self._compressedSize)
	def _backgroundGzip(self, compression):
		s = StringIO()
		gzipHandle = gzip.GzipFile(fileobj=s, mode='wb', compresslevel=compression)
		gzipHandle.write(self._compressible)
		gzipHandle.close()
		s = s.getvalue()
		with self._gzipLock:
			self._compressible = s
			self._compressedSize = len(s)
			self._gzipped = True

class diskCachedItem(_cachedItem):
	_cacheDirectory = None
	_maxFilenameSize = 92
	def __init__(self, cacheable):
		super(diskCachedItem, self).__init__(cacheable)
		encodedPath = u(base64.urlsafe_b64encode(self._key))
		encodedPathComponents = []
		while len(encodedPath):
			i = min(diskCachedItem._maxFilenameSize, len(encodedPath))
			encodedPathComponents.append(encodedPath[:i])
			encodedPath = encodedPath[i:]
		self._filename = os.path.join(diskCachedItem._cacheDirectory, *encodedPathComponents)
		dirname = os.path.dirname(self._filename)
		if not os.path.exists(dirname):
			os.makedirs(dirname)
		handlePristine = open(self._properFilename(False, forceGzip=False), 'wb')
		self._pristineSize = cacheable.writePristineTo(handlePristine)
		handlePristine.close()
		handleCompressible = open(self._properFilename(True, forceGzip=False), 'wb')
		self._compressibleSize = cacheable.writeCompressibleTo(handleCompressible)
		handleCompressible.close()
		self._finalize()
	def _properFilename(self, compressible, forceGzip=None):
		if not compressible:
			return self._filename + u'.prist.cache'
		if (self._gzipped and forceGzip is not False) or forceGzip:
			return self._filename + u'.gz.cache'
		return self._filename + u'.raw.cache'
	def toCacheable(self):
		with self._gzipLock:
			return cacheableItem(
				self._key,
				_streamableData(open(self._properFilename(False), 'rb'), knownSize=self._pristineSize, closeAfter=True),
				_streamableData(open(self._properFilename(True), 'rb'), knownSize=self._compressibleSize, closeAfter=True)
			)
	def getPristineData(self):
		data = ''
		handle = open(self._properFilename(False), 'rb')
		i = handle.read(_bufferSize)
		while len(i):
			data += i
			i = handle.read(_bufferSize)
		handle.close()
		return data
	def writePristineTo(self, target):
		handle = open(self._properFilename(False), 'rb')
		i = handle.read(_bufferSize)
		while len(i):
			target.write(i)
			i = handle.read(_bufferSize)
		handle.close()
		return self._pristineSize
	def getCompressibleData(self, waitForGzip=False):
		self._waitForGzip(waitForGzip)
		data = ''
		with self._gzipLock:
			handle = open(self._properFilename(True), 'rb')
			i = handle.read(_bufferSize)
			while len(i):
				data += i
				i = handle.read(_bufferSize)
			handle.close()
			return gzippedData(self._gzipped, data, knownSize=self._compressedSize)
	def writeCompressibleTo(self, target, waitForGzip=False):
		self._waitForGzip(waitForGzip)
		with self._gzipLock:
			handle = open(self._properFilename(True), 'rb')
			i = handle.read(_bufferSize)
			while len(i):
				target.write(i)
				i = handle.read(_bufferSize)
			handle.close()
			return (self._gzipped, self._compressedSize)
	def _backgroundGzip(self, compression):
		rawFile = self._properFilename(True, forceGzip=False)
		gzipFile = self._properFilename(True, forceGzip=True)
		gzipHandle = gzip.GzipFile(filename=gzipFile, mode='wb', compresslevel=compression)
		fHandle = open(rawFile, 'rb')
		i = fHandle.read(_bufferSize)
		while len(i):
			gzipHandle.write(i)
			i = fHandle.read(_bufferSize)
		fHandle.close()
		gzipHandle.close()
		with self._gzipLock:
			self._gzipped = True
			self._compressedSize = os.path.getsize(gzipFile)
			os.remove(rawFile)

class _cache(object):
	def __init__(self, name, totalSize, cachedClass, acceptUnknownSize=True, levelBelow=None):
		self._name = name
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
				cacheInfo(self._name, 'requires pruning; has', self._availableSpace, '/', self._totalSize, '; need', size)
				self._prune()
			self._availableSpace -= size
			self._items[item.getKey()] = item
			self._orderedItems.append(item)
	def lookup(self, key):
		if key in self._items:
			with self._lock:
				item = self._items[key]
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

def generateKey(*objects):
	s = []
	for i in objects:
		s.append(u(i).replace(u'\\', u'\\\\').replace(u';', u'\\;'))
	return u';'.join(s)

_fetchyCache = None

def init(gzipCompression, gzipMinSize, gzipMaxSize, diskCacheSize, memoryCacheSize, directory, bufferSize):
	global _bufferSize, _fetchyCache
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
		name='Memory',
		totalSize=memoryCacheSize,
		cachedClass=memoryCachedItem,
		acceptUnknownSize=False,
		levelBelow=_cache(
			name='Disk',
			totalSize=diskCacheSize,
			cachedClass=diskCachedItem
		)
	)
	cacheInfo('Cache initialized with configuration:', {
		'gzipCompression': gzipCompression,
		'gzipMinSize': gzipMinSize,
		'gzipMaxSize': gzipMaxSize,
		'diskCacheSize': diskCacheSize,
		'memoryCacheSize': memoryCacheSize,
		'directory': directory,
		'bufferSize': bufferSize
	})

def generateRequestKey(request):
	return generateKey(request.getCommand(), request.getUrl())

def lookupResponse(key):
	if _fetchyCache is None:
		return None
	data = _fetchyCache.lookup(key)
	if data is None:
		cacheInfo('[MISS] Cache lookup for', key, 'found nothing.')
	else:
		cacheInfo('[HIT] Cache lookup for', key, 'found match.')
		headers = httpRequest.headers(data.getPristineData())
		body = data.getCompressibleData(waitForGzip=True)
		if isinstance(body, _gzippedData):
			headers['Content-Encoding'] = body.getContentEncoding()
			body = body.getData()
		data = httpRequest.httpResponse(headers, body)
	return data

def cacheResponse(key, response):
	if _fetchyCache is None:
		return None
	cacheInfo('[ADD] Caching response at', key, response.getHeaders())
	_fetchyCache.add(_cacheableItem(key, u(response.getHeaders()), response.getData()))
