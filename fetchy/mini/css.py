from urlparse import urljoin
def process(document):
	soup = document.getSoup()
	styles = soup.findAll('style')
	linksStylesheets = soup.findAll('link', rel='stylesheet')
	result = ""
	for link in linksStylesheets:
		try: # if tag has attribute href
			src = script["href"]
			src = urlparse.urljoin(document.getUrl(), src)
			result += str(client.fetch(src))
		except:
			pass
	for style in styles:
		result += style.string
	result = "<style type=\"text/css\">" + result + "</style>"