import os, re, hashlib, subprocess, threading
from .. import httpRequest
from ..lib import BeautifulSoup
from ..lib.utils import *
from .. import client
from ..lib import cssCompiler


def init():
	pass

class _style(object):
	_removeHtmlComments = re.compile(u'^\\s*/*\\s*<!--[^\\r\\n]*|/*\\s*-->\\s*$')
	def __init__(self, document, key, text=None, url=None):
		self._document = document
		self._text = text
		self._url = url
		self._isText = self._text is not None
		if self._isText:
			self._text = _style._removeHtmlComments.sub(u'', self._text).strip()
			key.update('text' + self._text.encode('utf8'))
		else:
			key.update('url' + self._url.encode('utf8'))
	def writeTo(self, target):
		if self._isText:
			target(self._text)
		else:
			self._document.streamResourceTo(self._url, target)
			
class _combinedStyle(threading.Thread):
	def __init__(self):
		super(_combinedStyle, self).__init__()
		self._styles = []
		self._lock = threading.RLock()
		self._doneCondition = threading.Condition(self._lock)
		self._contents = u''
		self._doneProcessing = False
	def add(self, style):
		self._styles.append(style)
	def run(self):
		contents = ""
		for style in self._styles:
			if style._url is not None:
				contents+=str(client.fetch(style._url))
			if style._text is not None:
				contents+=style._text.encode('utf8')
		contents = cssCompiler.cssmin(contents)
		with self._lock:
			self._contents = contents
			self._doneProcessing = True
			self._doneCondition.notifyAll()
	def getData(self):
		with self._lock:
			while not self._doneProcessing:
				self._doneCondition.wait()
		return self._contents

def _getCombinedStyle(combinedStyle, key, url):
	data = combinedStyle.getData()
	return httpRequest.httpResponse({'content-type':'text/css'}, data, responseCode=200, finalUrl=url)

def process(document):
	soup = document.getSoup()
	body = soup('body')
	if not len(body):
		body = soup('html')
		if not len(body):
			return
	body = body[0]
	styles = soup('style')
	linksStylesheets = soup('link')
	if not len(styles) and not len(linksStylesheets):
		return
	combinedStyle = _combinedStyle()
	styleKey = hashlib.md5()
	for link in linksStylesheets:
		try:
			if(link['type'] == "text/css"):
				src = link['href']
				combinedStyle.add(_style(document, key=styleKey, url=document.resolveUrl(src)))
		except KeyError:
			pass
	for style in styles:		
		if hasattr(style, 'string') and style.string is not None:
			combinedStyle.add(_style(document, key=styleKey, text=style.string))
	combinedStyle.start()
	styleKey = styleKey.hexdigest() + u'.js'
	document.registerFakeResource(styleKey, curry(_getCombinedStyle, combinedStyle))
	styleTag = BeautifulSoup.Tag(soup, 'style', {'src': document.getFakeResourceUrl(styleKey)})
	for style in styles:
		style.extract()
	for link in linksStylesheets:
		link.extract()
	body.append(styleTag)
