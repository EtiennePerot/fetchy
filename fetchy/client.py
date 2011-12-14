import urllib2
import threading

class client:
    def __init__(self, url):
        self._url = url
    def run(self):
        html = urllib2.urlopen(self._url)
        print html.read()

class _runClient:
    def __init__(self):
        pass
    def run(self, url):
        _client = client(url)
        thread = threading.Thread(target=_client.run(), args=())
        thread.start()




