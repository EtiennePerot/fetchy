from ...lib.which import which
from ...lib._StringIO import StringIO
from ...lib.utils import *
from ...log import *
import os, threading, subprocess, tempfile

_enabled = False

class _jpegtran(threading.Thread):
	_jpegtranCommand = (
		'jpegtran',
		'-o',
		'-copy', 'none',
		'-progressive',
		'-outfile', '-'
	)
	_bufferSize = 16384
	def __init__(self, document, url):
		super(_jpegtran, self).__init__()
		self._document = document
		self._url = url
	def run(self):
		miniInfo('jpegtran running over', self._url)
		(tempHandle, tempName) = tempfile.mkstemp(prefix='fetchy-jpeg-', suffix='.jpg')
		self._document.streamResourceTo(self._url, curry(os.write, tempHandle))
		os.close(tempHandle)
		process = subprocess.Popen(
			_jpegtran._jpegtranCommand + (tempName,),
			_jpegtran._bufferSize,
			stdout=subprocess.PIPE
		)
		(data, _) = process.communicate()
		miniInfo('jpegtran returned', process.returncode, 'over', self._url)
		if not process.returncode:
			self._document.cacheResource(self._url, data, headers={'content-type': 'image/jpeg'})
		else:
			self._document.cancelResource(self._url)
		try:
			os.remove(tempName)
		except:
			pass

def process(document, image, url):
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
