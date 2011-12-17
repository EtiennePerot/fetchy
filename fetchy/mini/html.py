import css, js, images

def init(**kwargs):
	js.init(**kwargs['js'])
	css.init(**kwargs['css'])
	images.init(**kwargs['images'])

def process(document):
	js.process(document)
	css.process(document)
	images.process(document)
	return document
