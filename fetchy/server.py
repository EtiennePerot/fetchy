from log import *
from lib.utils import *
import httpHeaders
import fetchy
import urlparse, socket, threading, BaseHTTPServer, SocketServer, select, time

class _fetchyProxy(BaseHTTPServer.BaseHTTPRequestHandler):
	protocol_version = 'HTTP/1.1'
	_timeout = 10
	_bufferSize = 16384
	def _connect(self, server):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		address = (server, 80)
		splitPort = server.find(':')
		if splitPort != -1:
			address = server[:splitPort], int(server[splitPort + 1:])
		try:
			sock.connect(address)
		except socket.error, e:
			try:
				errMsg = e[1]
			except:
				errMsg = e
			self.send_error(404, 'Socket error: ' + u(errMsg))
			return None
		return sock
	def _passthrough(self, destinationSocket):
		connection = self.connection
		inputs = [connection]
		outputs = []
		keepGoing = True
		initialTime = time.time()
		while keepGoing:
			try:
				(inStreams, _, errStreams) = select.select(inputs, outputs, inputs, _fetchyProxy._timeout)
				if errStreams:
					break
				if len(inStreams):
					data = connection.recv(16384)
					if data:
						destinationSocket.send(data)
						initialTime = time.time()
			except:
				break
			keepGoing = time.time() - initialTime < _fetchyProxy._timeout
	def _spawnSender(self, destinationSocket):
		threading.Thread(self._passthrough(destinationSocket)).start()
	def do_GET(self):
		serverInfo('Got request:', self.command, self.path, 'on', threading.current_thread().name)
		(scheme, netloc, path, params, query, fragment) = urlparse.urlparse(self.path, 'http')
		headers = httpHeaders.headers(self.headers)
		keepAlive = headers.isKeepAlive()
		if scheme != 'http' or fragment or not netloc:
			self.send_error(400, "Invalid url: " + self.path)
			return
		try:
			del headers['Connection']
			response = fetchy.handleRequest(self.path, headers)
			if response is None:
				serverWarn('Error happened while serving', self.path)
				self.send_error(500, 'Error happened somewhere in fetchy.')
			else:
				serverInfo('Served', self.path, 'with', len(response), 'bytes')
				self.connection.send(response)
		except IOError:
			pass
		finally:
			if not keepAlive:
				try:
					self.connection.close()
				except:
					pass

class _threadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
	pass

class _runThread(threading.Thread):
	def __init__(self, server):
		super(_runThread, self).__init__()
		self._server = server
	def run(self):
		self._server.serve_forever()

def init(port, reverseProxy, timeout, bufferSize):
	serverInfo('Starting server...')
	_fetchyProxy._timeout = timeout
	_fetchyProxy._bufferSize = bufferSize
	server = _threadedHTTPServer(('', port), _fetchyProxy)
	serverInfo('Server listening on socket', server.socket.getsockname())
	_runThread(server).start()
	serverInfo('Server thread spawned.')
