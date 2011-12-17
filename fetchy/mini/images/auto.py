import bmp, jpeg, png, tga

def auto(image):
	pass # Todo: Detect format, pass to appropriate module

def process(document):
	soup = document.getSoup()
	url = document.getUrl()
	images = soup.findAll('img')
	for image in images:
	        if(str(image["src"])[0] is "/"):#if image reference is relative
	            if("http://" in url):
	                tmp_int = url[7:].find("/")
	                if(tmp_int >= 0):#if there is a 3rd occurence of "/" in "url"
	                    document.addResource(url[:7 + tmp_int] + image["src"])
	                else:
	                    document.addResource(url + "/" + image["src"])
	            else:
	                tmp_int = url.find("/")
	                if(tmp_int >= 0):#if there is an occurence of "/" in "url"
	                    document.addResource(url[:tmp_int] + image["src"])
	                else:
	                    document.addResource(url + "/" + image["src"])
	        else:
	            document.addResource(image["src"])
	    #TODO put in cache, jpegtran, pngcrush, transform bmp and tga images
