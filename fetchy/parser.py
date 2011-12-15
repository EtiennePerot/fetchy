from lib import BeautifulSoup
import client

def parse(url):
    client.asyncFetch(url, onSuccess=processHTML)
def processHTML(html):
    soup = BeautifulSoup.BeautifulSoup(html.getData())
    javascriptContent = soup.findAll('script')
    cssContent = soup.findAll('link', rel='stylesheet')
    images = soup.findAll('img')
    print images, cssContent, javascriptContent #test
def parseJavascript(content):
    pass
    #TODO concatenation, minification, compression, prefetch
def parseCSS(content):
    pass
    #TODO concatenation, minification, compression, prefetch
def parseImg(content):
    pass
    #TODO prefetch, jpegtran, pngcrush, transform bmp and tga images
def parseHTML(content):
    pass
    #TODO minification 
        

parse("http://google.com")
    
    

