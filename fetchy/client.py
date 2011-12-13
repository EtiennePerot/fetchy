import urllib2
class Client:
    _isReady = False
    def asyncFetch(url):
        html = urllib2.urlopen(url)
        print html.read()
    def isReady():
        return _isReady
