import cache

_responseCallback = None

def cacheResponse(key, response):
	if key is not None and response is not None:
		cache.cacheResponse(key, response.toFetchyResponse())

def _backgroundCache(request):
	key = cache.generateRequestKey(request)
	response = _responseCallback(request)
	if response is None:
		cache.cancel(key)
	else:
		cacheResponse(key, response)

def reserveRequest(request):
	cacheKey = cache.generateRequestKey(request)
	if cacheKey is not None:
		return cache.reserve(cacheKey)
	return False

def cancelRequest(request):
	cacheKey = cache.generateRequestKey(request)
	if cacheKey is not None:
		return cache.cancel(cacheKey)
	return False

def backgroundCache(request):
	if reserveRequest(request):
		threading.Thread(target=curry(_backgroundCache, request)).start()
	return True

def init(responseCallback):
	global _responseCallback
	_responseCallback = responseCallback
