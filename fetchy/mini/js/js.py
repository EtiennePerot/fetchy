import os, re, hashlib, subprocess, threading
from ... import httpRequest
from ...lib import BeautifulSoup
from ...lib.utils import *
from ...lib.which import which
from ...lib._StringIO import StringIO
from ...log import *

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
	def getData(self):
		if self._isText:
			return self._text
		s = StringIO()
		self._document.streamResourceTo(self._url, s)
		return s.getvalue()
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
		if _combinedScript._useCompiler:
			process = subprocess.Popen(
				_combinedScript._compilerCommand1 + [_combinedScript._compilerLevel] + _combinedScript._compilerCommand2,
				- 1,
				stdin=subprocess.PIPE,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE
			)
			for script in self._scripts:
				script.writeTo(process.stdin.write)
				process.stdin.write(';\n')
			contents = process.communicate()
			if not process.returncode:
				contents = contents[0].decode('utf8').strip()
				return
			# If the process didn't return 0, continue and use regular string method
		contents = u''
		for script in self._scripts:
			contents += u(script.getData()).strip() + u';\n'
		contents = contents.strip()
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

_enabled = True

def process(document):
	soup = document.getSoup()
	scripts = soup('script')
	if not len(scripts):
		return
	body = soup('body')
	if not len(body):
		body = soup('html')
		if not len(body):
			return
	body = body[0]
	if _enabled:
		combinedScript = _combinedScript()
		scriptKey = hashlib.md5()
		for script in scripts:
			try:
				combinedScript.add(_script(document, key=scriptKey, url=document.resolveUrl(script['src'])))
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
	else:
		for script in scripts:
			try:
				document.addResource(document.resolveUrl(script['src']))
			except KeyError:
				continue

def init(enabled, closureLevel):
	global _enabled
	_enabled = enabled
	if not _enabled:
		miniInfo('Closure compiler disabled, JS concatenation disabled.')
		return
	if closureLevel is None:
		miniInfo('Closure compiler disabled, but JS concatenation still enabled.')
		combinedScript._useCompiler = False
		return
	java = which('java')
	if not java:
		java = which('javaw')
		if not java:
			_combinedScript._useCompiler = False
			miniWarn('java not found in PATH! The Closure compiler will be disabled.')
			return
	_combinedScript._useCompiler = closureLevel in ('WHITESPACE_ONLY', 'SIMPLE_OPTIMIZATIONS', 'ADVANCED_OPTIMIZATIONS')
	if _combinedScript._useCompiler:
		_combinedScript._compilerLevel = closureLevel
		miniInfo('java found at', java, '- Closure compiler enabled with level', closureLevel)
	else:
		miniWarn('Closure compiler was given a wrong level:', closureLevel)
