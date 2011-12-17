import css, js, images
from ..lib import BeautifulSoup

def init(**kwargs):
	js.init(**kwargs['js'])
	#css.init(**kwargs['css'])
	images.init(**kwargs['images'])

def process(document):
	js.process(document)
	css.process(document)
	images.process(document)
	for comment in document.getSoup().findAll(text=lambda x:isinstance(x, BeautifulSoup.Comment)):
		comment.extract()
	return document
