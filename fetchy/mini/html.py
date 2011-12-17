import css, js, images

def process(document):
	js.process(document)
	css.process(document)
	images.process(document)
	return document
