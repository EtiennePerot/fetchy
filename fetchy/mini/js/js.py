import os, re, hashlib, subprocess, threading
from ... import httpRequest
from ...lib import BeautifulSoup
from ...lib.utils import *

class _script(object):
	_removeHtmlComments = re.compile(u'^\\s*/*\\s*<!--[^\\r\\n]*|/*\\s*-->\\s*$')
	def __init__(self, document, key, text=None, url=None):
		self._document = document
		self._text = text
		self._url = url
		self._isText = self._text is not None
		if self._isText:
			self._text = _script._removeHtmlComments.sub(u'', self._text).strip()
			key.update('text' + self._text.encode('utf8'))
		else:
			key.update('url' + self._url.encode('utf8'))
	def writeTo(self, target):
		if self._isText:
			target(self._text)
		else:
			self._document.streamResourceTo(self._url, target)

class _combinedScript(threading.Thread):
	_useCompiler = True
	_compilerCommand1 = [
		'java', '-jar', os.path.join(os.path.dirname(os.path.realpath(__file__)), 'closure', 'compiler.jar'),
		'--accept_const_keyword',
		'--charset', 'UTF-8',
		'--compilation_level'
	]
	_compilerLevel = 'SIMPLE_OPTIMIZATIONS'
	_compilerCommand2 = [
		'--logging_level', 'OFF',
		'--warning_level', 'QUIET'
	]
	def __init__(self):
		super(_combinedScript, self).__init__()
		self._scripts = []
		self._lock = threading.RLock()
		self._doneCondition = threading.Condition(self._lock)
		self._contents = u''
		self._doneProcessing = False
	def add(self, script):
		self._scripts.append(script)
	def run(self):
		process = subprocess.Popen(
			_combinedScript._compilerCommand1 + [combinedScript._compilerLevel] + combinedScript._compilerCommand2,
			- 1,
			stdin=subprocess.PIPE,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE
		)
		for script in self._scripts:
			script.writeTo(process.stdin.write)
			process.stdin.write(';')
		(contents, _) = process.communicate()
		contents = contents.decode('utf8').strip()
		with self._lock:
			self._contents = contents
			self._doneProcessing = True
			self._doneCondition.notifyAll()
	def getData(self):
		with self._lock:
			while not self._doneProcessing:
				self._doneCondition.wait()
		return self._contents

def _getCombinedScript(combinedScript, key, url):
	data = combinedScript.getData()
	return httpRequest.httpResponse({'content-type':'text/javascript'}, data, responseCode=200, finalUrl=url)

def process(document):
	soup = document.getSoup()
	body = soup('body')
	if not len(body):
		body = soup('html')
		if not len(body):
			return
	scripts = soup('script')
	if not len(scripts):
		return
	body = body[0]
	combinedScript = _combinedScript()
	scriptKey = hashlib.md5()
	for script in scripts:
		try:
			src = script['src']
			combinedScript.add(_script(document, key=scriptKey, url=document.resolveUrl(src)))
		except KeyError:
			if hasattr(script, 'string') and script.string is not None:
				combinedScript.add(_script(document, key=scriptKey, text=script.string))
	combinedScript.start()
	scriptKey = scriptKey.hexdigest() + u'.js'
	document.registerFakeResource(scriptKey, curry(_getCombinedScript, combinedScript))
	scriptTag = BeautifulSoup.Tag(soup, u'script', {u'src': document.getFakeResourceUrl(scriptKey)})
	scriptTag.append(BeautifulSoup.NavigableString(u''))
	wrapperDiv = BeautifulSoup.Tag(soup, u'div', {u'style': u'display:none'})
	wrapperDiv.append(scriptTag)
	for script in scripts:
		script.extract()
	body.append(wrapperDiv)

def init(closureLevel):
	_combinedScript._useCompiler = closureLevel in ('WHITESPACE_ONLY', 'SIMPLE_OPTIMIZATIONS', 'ADVANCED_OPTIMIZATIONS')
	if _combinedScript._useCompiler:
		_combinedScript._compilerLevel = closureLevel
