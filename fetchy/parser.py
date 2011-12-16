from lib import BeautifulSoup
from lib import closure
import client
import re

def parse(url):
    client.asyncFetch(url, onSuccess=processHTML)
    
def processHTML(html):
    soup = BeautifulSoup.BeautifulSoup(html.getData())
    javascriptContent = soup.findAll('script', type="text/javascript")
    parseJavascript(javascriptContent, html.getFinalUrl())
    cssContent = soup.findAll('style', type="text/css")
    parseCSS(cssContent)
    images = soup.findAll('img')
    
def parseJavascript(content, url):
    #concatenate tags
    result = ''
    for script in content:
        script_string = str(script)
        opening_tag = script_string[:script_string.index(">")]
        if(re.search('src\s*=', opening_tag) is None):#if tag doesn't have src attribute
            start = script_string.index('>') + 1
            end = script_string.index("</script>")
            result += script_string[start:end]
        else:
            print script#TODO fetch, concatenate

    #compression and minification
    result = closure.compressJavascript(result)
    
    print result
    
    #TODO concatenation, prefetch
def parseCSS(content):
    #concatenate tags
    result = '<style type="text/css">'
    for style in content:
        start = str(style).index('>') + 1
        end = str(style).index('</style>')
        result += str(style)[start:end]
    result += "</style>"
    #TODO concatenation, minification, compression, prefetch
def parseImg(content):
    pass
    #TODO prefetch, jpegtran, pngcrush, transform bmp and tga images
def parseHTML(content):
    pass
    #TODO minification 
        

parse("http://www.w3schools.com/js/js_howto.asp")
#parse("http://www.w3schools.com/css/tryit.asp?filename=trycss_default")
    
    

