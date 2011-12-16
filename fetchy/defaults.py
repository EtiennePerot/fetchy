# Default fetchy settings
config = {
	'verbose': False, # Verbose mode on or off
	'quiet': False, # True to make the process completely quiet
	'server': { # Options related to the listening server
		'port': 9010, # Port to listen on
		'reverseProxy': None, # If fetchy is meant to be used as a reverse proxy, this should contain the hostname:portNumber of the actual web server behind it.
		'timeout': 5.0, # Timeout to wait for client uploading data to proxy (seconds)
		'chunkSize': 16384, # Chunk size to use when transmitting data back to client
		'bufferSize': 1024, # Buffer size for server forwarding data to client (bytes)
	},
	'client': { # Options related to the HTTP client
		'timeout': 5.0, # Timeout for outgoing HTTP requests (seconds)
		'bufferSize': 16384, # Buffer size for client HTTP requests (bytes)
	},
	'cache': { # Options related to the cache
		'gzipCompression': 6, # Strength of gzip compression for cached files (from 0 (don't use compression) to 9 (best compression))
		'gzipMinSize': 128, # Minimum size (in bytes) for gzip compression to be valuable
		'gzipMaxSize': 128 * 1024 * 1024, # Maximum size (in bytes) after which gzip compression becomes too expensive (large files are likely to be in a compressed format already)
		'diskCacheSize': 128 * 1024 * 1024, # Disk cache size (bytes)
		'memoryCacheSize': 32 * 1024 * 1024, # Memory cache size (bytes)
		'directory': '%tmp%/fetchy', # Location of the disk cache ("%tmp%" will be replaced by the system's temporary directory)
		'bufferSize': 32768, # Buffer size for cache I/O operations
	}
}
