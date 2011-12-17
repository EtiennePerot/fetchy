import css, js, images

def process(document):
	js.process(document)
	css.process(document)
	images.process(document)
	content = ' '.join(unicode(document.getSoup()).split())
	return content
