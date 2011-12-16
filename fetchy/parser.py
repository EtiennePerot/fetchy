from lib import BeautifulSoup
from lib import closure
import client
import string

def parse(url):
    client.asyncFetch(url, onSuccess=processHTML)
    
def processHTML(html):
    soup = BeautifulSoup.BeautifulSoup(html.getData())
    javascriptContent = soup.findAll("script", type="text/javascript")
    parseJavascript(javascriptContent, html.getUrl())
    cssContent = soup.findAll("link", type="text/css")
    cssContent.append(soup.findAll("style", type="text/css"))
    parseCSS(cssContent)
    images = soup.findAll("img")
    parseImg(images, html.getUrl())
    
def parseJavascript(content, url):
    #concatenate and fetch content
    result = ""
    for script in content:
        try:#if tag has attribute source
            src = script["src"]
            result += str(client.fetch(src))
        except:
            result += script.string

    #compression and minification
    result = closure.compressJavascript(result)
    result = "".join(["<script type=\"text/javascript\">",result,"</script>"])
    print result  
        
def parseCSS(content):
    for tag in content:
        try:#if tag has attribute source
            src = tag["href"]
            client.asyncFetch(src)
        except:
            pass
        
def parseImg(content, url):
    for image in content:
        if(str(image["src"])[0] is "/"):#if image reference is relative
            if("http://" in url):
                tmp_int = url[7:].index("/")
                if(tmp_int >= 0):#if there is a 3rd occurence of "/" in "url"
                    client.asyncFetch(url[:7+tmp_int]+image["src"])
                else:
                    client.asyncFetch(url+"/"+image["src"])
            else:
                tmp_int = url.index("/")
                if(tmp_int >= 0):#if there is an occurence of "/" in "url"
                    client.asyncFetch(url[:tmp_int]+image["src"])
                else:
                    client.asyncFetch(url+"/"+image["src"])
        else:
            client.asyncFetch(image["src"])
    #TODO put in cache, jpegtran, pngcrush, transform bmp and tga images
    
def parseHTML(content):
     content = string.join(content.split()," ")
     print content
        

parse("http://stackoverflow.com/questions/1883980/find-the-nth-occurrence-of-substring-in-a-string")
#parse("http://www.w3schools.com/tags/tag_script.asp")
    

