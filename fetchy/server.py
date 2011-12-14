from log import *
from lib.utils import *
import urlparse, socket, threading, BaseHTTPServer, SocketServer

class _fetchyProxy(BaseHTTPServer.BaseHTTPRequestHandler):
	protocol_version = 'HTTP/1.1'
	def do_GET(self):
		serverInfo('Got request:', self.path)
		self.connection.close()

class _threadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
	pass

class _runThread(threading.Thread):
	def __init__(self, server):
		super(_runThread, self).__init__()
		self._server = server
	def run(self):
		self._server.serve_forever()

def run(port):
	serverInfo('Starting server...')
	server = _threadedHTTPServer(('', port), _fetchyProxy)
	serverInfo('Server listening on socket', server.socket.getsockname())
	_runThread(server).start()
	serverInfo('Server thread spawned.')
