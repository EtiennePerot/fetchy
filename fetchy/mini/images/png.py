from ...lib.which import which
from ...lib._StringIO import StringIO
from ...lib.utils import *
from ...log import *
import os, threading, subprocess, tempfile

_enabled = False

class _pngout(threading.Thread):
	_pngoutCommand1 = (
		'pngout',
	)
	_pngoutStrategy = '-s2'
	_pngoutCommand2 = (
		'-y',
		'-q'
	)
	_bufferSize = 16384
	def __init__(self, document, url):
		super(_pngout, self).__init__()
		self._document = document
		self._url = url
	def run(self):
		miniInfo('pngout running over', self._url)
		(tempHandle, tempName) = tempfile.mkstemp(prefix='fetchy-png-', suffix='.png')
		try:
			self._document.streamResourceTo(self._url, curry(os.write, tempHandle))
			os.close(tempHandle)
			process = subprocess.Popen(
				_pngout._pngoutCommand1 + (_pngout._pngoutStrategy,) + _pngout._pngoutCommand2 + (tempName, '-'),
				_pngout._bufferSize,
				stdout=subprocess.PIPE
			)
			(data, _) = process.communicate()
			miniInfo('pngout returned', process.returncode, 'over', self._url)
			if not process.returncode or process.returncode == 2: # pngout returns 2 when it didn't change the file size, but the result is still valid
				self._document.cacheResource(self._url, data, headers={'content-type': 'image/png'})
			else:
				self._document.cancelResource(self._url)
		finally:
			try:
				os.remove(tempName)
			except:
				pass

def process(document, image, url):
	if not _enabled:
		return False
	return _pngout(document, url).start

def init(pngoutStrategy, bufferSize):
	global _enabled
	if pngoutStrategy is None:
		miniInfo('pngout disabled.')
		_enabled = False
		return
	pngout = which('pngout')
	if not pngout:
		miniWarn('pngout not found in PATH! pngout disabled.')
		_enabled = False
		return
	miniInfo('pngout found at', pngout, '- pngout enabled.')
	_enabled = True
	_pngout._bufferSize = bufferSize
	_pngout._pngoutStrategy = '-s' + str(pngoutStrategy)
