__all__ = ['html', 'css', 'js', 'images']

import html, urlparse, threading, re
from ..lib.slimmer import html_slimmer
from ..lib import BeautifulSoup
from ..lib.utils import *
from .. import client
from ..fetchy import *
from .. import cache
from .. import httpRequest
from .. import parser

class _document(object):
    def __init__(self, response):
        self._response = response
        self._url = u(self._response.getUrl())
        self._data = html_slimmer(self._response.getData())
        self._soup = BeautifulSoup.BeautifulSoup(self._data)
        self._fakeResources = {}
        self._resources = []
    def getUrl(self):
        return self._url
    def getResponse(self):
        return self._response
    def getData(self):
        return self._data
    def getSoup(self):
        return self._soup
    def resolveUrl(self, url):
        return urlparse.urljoin(self._url, u(url))
    def _getResourceRequest(self, resource):
        return httpRequest.httpRequest('GET', resource)
    def addResource(self, resource):
        if resource not in self._resources:
            self._resources.append(resource)
            backgroundCache(self._getResourceRequest(resource))
            return True
        return False
    def reserveResource(self, resource):
        if resource not in self._resources:
            self._resources.append(resource)
            return fetchy.reserveRequest(self._getResourceRequest(resource))
        return False
    def cancelResource(self, resource):
        if resource in self._resources:
            return fetchy.cancelRequest(self._getResourceRequest(resource))
    def cacheResource(self, resource, data, headers={}, responseCode=200):
        if resource in self._resources:
            response = httpRequest.httpResponse(headers, data, finalUrl=resource, responseCode=responseCode)
            return fetchy.cacheResponse(cache.generateRequestKey(self._getResourceRequest(resource)), response)
    def streamResourceTo(self, resource, target, **kwargs):
        client.fetch(resource, toFeed=target, **kwargs)
    def registerFakeResource(self, key, callback):
        parser._fetchyResourceManager.add(key, callback)
    def getFakeResourceUrl(self, key):
        return u'http://fetchy/' + u(key)
    def __enter__(self):
        self._soupLock.acquire()
    def __exit__(self):
        self._soupLock.release()

process = html.process
init = html.init
