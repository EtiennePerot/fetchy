import css, js, images
from ..lib import BeautifulSoup, slimmer
from ..log import *

def process(document):
	js.process(document)
	css.process(document)
	images.process(document)
	for comment in document.getSoup().findAll(lambda x : isinstance(x, BeautifulSoup.Comment)):
		comment.extract()
	return document

_enabled = True
_hardcore = True
def minify(html):
	if not _enabled:
		return html
	return slimmer.slimmer(html, hardcore=_hardcore)

def init(**kwargs):
	global _enabled, _hardcore
	_enabled = kwargs['html']['enabled']
	_hardcore = kwargs['html']['hardcore']
	miniVerbose(kwargs['verbose'])
	js.init(**kwargs['js'])
	css.init(**kwargs['css'])
	images.init(**kwargs['images'])
