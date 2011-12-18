from ...log import *
from ...lib._StringIO import StringIO
import png
import threading

try:
	import Image
except ImportError:
	Image = None

class _converter(threading.Thread):
	def __init__(self, formatName, urlTransform, document, image, url):
		super(_converter, self).__init__()
		self._document = document
		self._image = image
		self._url = url
		self._formatName = formatName
		self._newUrl = urlTransform(self._url)
		self._pngHandler = png.process(self._document, self._image, self._newUrl)
	def isReady(self):
		return self._pngHandler
	def start(self):
		self._image['src'] = self._newUrl
		self._document.reserveResource(self._newUrl)
		super(_converter, self).start()
	def run(self):
		miniInfo('Converting', self._formatName, '-> PNG:', self._url)
		try:
			rawData = StringIO()
			self._document.streamResourceTo(self._url, rawData.write)
			rawData.seek(0)
			tga = Image.open(rawData)
			del rawData
			output = StringIO()
			tga.save(output, 'png')
			output = output.getvalue()
			miniInfo(self._formatName, 'conversion successful for', self._url, '- Passing to PNG handler')
			self._pngHandler()
		except:
			miniInfo(self._formatName, 'conversion failed for', self._url)
			self._document.cancelResource(self._url)

class buildConverter(object):
	def __init__(self, formatName, urlTransform):
		self._formatName = formatName
		self._urlTransform = urlTransform
		self._enabled = False
	def process(self, *args, **kwargs):
		if not self._enabled:
			return False
		converter = _converter(self._formatName, self._urlTransform, *args, **kwargs)
		if not converter.isReady():
			return False
		return converter.start
	def init(self, enabled):
		self._enabled = enabled and Image is not None
		if not enabled:
			miniInfo('TGA ->', self._formatName, 'conversion is disabled.')
			return
		if Image is None:
			miniWarn('PIL is not installed! ', self._formatName, '-> PNG conversion will be disabled.')
			return
		miniInfo(self._formatName, '-> PNG conversion is enabled.')
