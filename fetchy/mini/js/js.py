import os, re, hashlib, subprocess, threading
from lib import BeautifulSoup
from lib.utils import *

class _script(object):
	_removeHtmlComments = re.compile(u'^\\s*/*\\s*<!--[^\\r\\n]*|/*\\s*-->\\s*$')
	def __init__(self, document, key, text=None, url=None):
		self._document = document
		self._text = text
		self._url = url
		self._isText = self._text is not None
		if self._isText:
			self._text = _script._removeHtmlComments.sub(u'', self._text).strip()
			key.update(u'text' + self._text)
		else:
			key.update(u'url' + self._url)
	def writeTo(self, target):
		if self._isText:
			target(self._text)
		else:
			self._document.streamResourceTo(self._url, target)

class _combinedScript(threading.Thread):
	_compilerCommand = [
		'java', '-jar', os.path.join(os.path.dirname(os.path.realpath(__file__)), 'closure', 'compiler.jar'),
		'--accept_const_keyword',
		'--charset', 'UTF-8',
		'--compilation_level', 'SIMPLE_OPTIMIZATIONS',
		'--logging_level', 'OFF',
		'--warning_level', 'QUIET'
	]
	def __init__(self):
		super(_combinedScript, self).__init__()
		self._scripts = []
		self._doneAdding = False
		self._lock = threading.RLock()
		self._event = threading.Condition(self._lock)
		self._contents = u''
		self._process = subprocess.Popen(_combinedScript._compilerCommand, -1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		self._doneProcessing = False
		self.start()
	def add(self, script):
		with self._lock:
			self._scripts.append(script)
			self._event.notifyAll()
	def doneAdding(self):
		with self._lock:
			self._doneAdding = True
			self._event.notifyAll()
	def run(self):
		self._lock.acquire()
		while not self._doneAdding or len(self._scripts):
			while not self._doneAdding and not len(self._scripts):
				self._event.wait()
			if self._doneAdding and not len(self._scripts):
				break
			script = self._scripts.pop(0)
			self._lock.release()
			script.writeTo(self._process.stdin.write)
			self._process.stdin.write(';')
			self._lock.acquire()
		(self._contents, _) = self._process.communicate()
		self._contents = self._contents.decode('utf8').strip()
		self._doneProcessing = True
		self._event.notifyAll()
		self._lock.release()
	def getData(self):
		with self._lock:
			while not self._doneProcessing:
				self._event.wait()
		return self._contents

def _getCombinedScript(combinedScript, *args):
	return _getCombinedScript.getData()

def process(document):
	soup = document.getSoup()
	body = soup('body')
	if not len(body):
		body = soup('html')
		if not len(body):
			return
	body = body[0]
	scripts = soup('script')
	combinedScript = _combinedScript()
	scriptKey = hashlib.md5()
	for script in scripts:
		if 'src' in script:
			combinedScript.add(_script(document, key=scriptKey, url=document.resolveUrl(script['src'])))
		elif hasattr(script, 'string'):
			combinedScript.add(_script(document, key=scriptKey, text=script['text']))
	combinedScript.doneAdding()
	scriptKey = u'js-' + scriptKey.hexdigest()
	document.registerFakeResource(scriptKey, curry(_getCombinedScript, combinedScript))
	scriptTag = BeautifulSoup.Tag(soup, 'script', {'src': document.getFakeResourceUrl(scriptKey)})
	for script in scripts:
		script.extract()
	body.append(scriptTag)
