def process(document):
	soup = document.getSoup()
	styles = soup.findAll('style')
	linksStylesheets = soup.findAll('link', rel='stylesheet')
	# todo
