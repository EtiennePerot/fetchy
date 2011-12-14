# Default fetchy settings
config = {
	'verbose': False, # Verbose mode on or off
	'quiet': False, # True to make the process completely quiet
	'server': { # Options related to the listening server
		'port': 9010, # Port to listen on
		'clientTimeout': 5.0, # Timeout to wait for client uploading data to proxy (seconds)
		'bufferSize': 1024, # Buffer size for server forwarding data to client (bytes)
	},
	'client': { # Options related to the HTTP client
		'httpTimeout': 5.0, # Timeout for outgoing HTTP requests (seconds)
		'bufferSize': 16384, # Buffer size for client HTTP requests (bytes)
	},
	'cache': { # Options related to the cache
		'gzipCompression': 6, # Strength of gzip compression for cached files (from 0 (don't use compression) to 9 (best compression))
		'diskCacheSize': 128 * 1024 * 1024, # Disk cache size (bytes)
		'memoryCacheSize': 32 * 1024 * 1024, # Memory cache size (bytes)
		'directory': '%tmp%/fetchy', # Location of the disk cache ("%tmp%" will be replaced by the system's temporary directory)
		'bufferSize': 32768,
	}
}
