import httplib, urllib, sys

# Define the parameters for the POST request and encode them in
# a URL-safe format.
def compressJavascript(script):
    params = urllib.urlencode([('js_code', script), ('compilation_level', 'SIMPLE_OPTIMIZATIONS'), ('output_format', 'text'), ('output_info', 'compiled_code'), ])
    # Always use the following value for the Content-type header.
    headers = { "Content-type": "application/x-www-form-urlencoded" }
    conn = httplib.HTTPConnection('closure-compiler.appspot.com')
    conn.request('POST', '/compile', params, headers)
    response = conn.getresponse()
    data = response.read()
    conn.close
    return data

def process(document):
	#concatenate and fetch content
	scripts = document.getSoup().findAll('script')
	result = ""
	for script in scripts:
		try: # if tag has attribute source
			src = script["src"]
			result += str(client.fetch(src))
		except:
			if script.string is not None:
				tmp_int = script.string.find("<!--")
				if(tmp_int < 0):#if there are no invalid elements for compression
					result += script.string
				else:
					result += script.string[tmp_int + 4:script.string.find("-->")]
    #compression and minification
	result = compressJavascript(result)
	result = '<script type="text/javascript">' + result + '</script>'
