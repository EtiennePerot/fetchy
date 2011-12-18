from log import *
from lib.utils import *
import httpRequest
import fetchy
import urlparse, socket, threading, BaseHTTPServer, SocketServer, select, time

class _bufferedWriter(object):
	def __init__(self, stream, writeFunction=None, buffer=4096):
		self._stream = stream
		if writeFunction is not None:
			self._writeFunction = writeFunction
		elif hasattr(self._stream, 'write'):
			self._writeFunction = self._stream.write
		elif hasattr(self._stream, 'send'):
			self._writeFunction = self._stream.send
		self._toWrite = ''
		self._bufferSize = buffer
		self._callFlush = hasattr(self._stream, 'flush')
	def write(self, data):
		self._toWrite += data
		while len(self._toWrite) >= self._bufferSize:
			self.flush()
	def flush(self):
		index = min(self._bufferSize, len(self._toWrite))
		self._writeFunction(self._toWrite[:index])
		self._toWrite = self._toWrite[index:]
		if self._callFlush:
			self._stream.flush()
	def close(self):
		self._stream.close()

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
	def handle_one_request(self): # Workaround Python bug in BaseHTTPRequestHandler
		try:
			BaseHTTPServer.BaseHTTPRequestHandler.handle_one_request(self)
		except AttributeError:
			self.close_connection = 1
	def _initRequest(self):
		serverInfo(self.command, self.path, 'on', threading.current_thread().name)
		(scheme, netloc, path, params, query, fragment) = urlparse.urlparse(self.path, 'http')
		if scheme != 'http' or fragment or not netloc:
			self.send_error(400, 'Invalid url: ' + self.path)
	def _writeResponse(self, response):
		if response is None:
			serverWarn('Error happened while serving', self.path)
			self.send_error(500, 'Error happened somewhere in fetchy.')
		else:
			writer = _bufferedWriter(self.wfile, buffer=_fetchyProxy._bufferSize)
			size = response.writeTo(writer.write)
			writer.flush()
			serverInfo('Served', self.path, '(Total', size, 'bytes)')
	def do_GET(self):
		self._initRequest()
		try:
			request = httpRequest.httpRequest(self.command, self.path, self.headers)
			response = fetchy.handleRequest(request)
			self._writeResponse(response)
		except IOError:
			pass
		finally:
			try:
				self.finish()
			except:
				pass
	def do_POST(self):
		self._initRequest()
		try:
			headers = httpRequest.headers(self.headers)
			contentLength = headers['Content-Length']
			if contentLength is None:
				self.send_error(406, 'POST request must include Content-Length header.')
				return
			try:
				contentLength = int(contentLength)
			except ValueError:
				self.send_error(406, 'Content-Length header is not an integer.')
				return
			data = self.rfile.read(contentLength)
			request = httpRequest.httpRequest(self.command, self.path, headers, data)
			response = fetchy.handleRequest(request)
			self._writeResponse(response)
		except IOError:
			pass
		finally:
			try:
				self.finish()
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

def init(port, reverseProxy, timeout, chunkSize, bufferSize):
	serverInfo('Starting server...')
	_fetchyProxy._timeout = timeout
	_fetchyProxy._bufferSize = bufferSize
	httpRequest.init(chunkSize=chunkSize)
	server = _threadedHTTPServer(('', port), _fetchyProxy)
	serverInfo('Server listening on socket', server.socket.getsockname())
	_runThread(server).start()
	serverInfo('Server thread spawned.')
