from ...lib.which import which
from ...log import *
import threading, subprocess

_enabled = False

class _jpegtran(threading.Thread):
	_jpegtranCommand = [
		'jpegtran',
		'-o',
		'-copy', 'none',
		'-progressive'
	]
	_bufferSize = 16384
	def __init__(self, document, url):
		super(_jpegtran, self).__init__()
		self._document = document
		self._url = url
	def run(self):
		miniInfo('jpegtran running over', self._url)
		process = subprocess.Popen(
			_jpegtran._jpegtranCommand,
			_jpegtran._bufferSize,
			stdin=subprocess.PIPE,
			stdout=subprocess.PIPE
		)
		def close(*args):
			process.stdin.close()
		self._document.streamResourceTo(self._url, process.stdin.write, synchronous=False, onSuccess=close, onFailure=close)
		data = ''
		while process.poll() is None:
			data += process.stdout.read(_jpegtran._bufferSize)
		if not process.returncode:
			self._document.cacheResource(self._url, data, headers={'content-type': 'image/jpeg'})
		else:
			self._document.cancelResource(self._url)

def process(document, url):
	if not _enabled:
		return False
	return _jpegtran(document, url).start

def init(useJpegtran, bufferSize):
	global _enabled
	if not useJpegtran:
		miniInfo('jpegtran disabled.')
		_enabled = False
		return
	jpegtran = which('jpegtran')
	if not jpegtran:
		miniWarn('jpegtran not found in PATH! jpegtran disabled.')
		_enabled = False
		return
	miniInfo('jpegtran found at', jpegtran, '- jpegtran enabled.')
	_enabled = True
	_jpegtran._bufferSize = bufferSize
