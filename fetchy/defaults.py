# Default fetchy settings
config = {
	'quiet': False, # True to make the process completely quiet
	'verbose': False, # Verbose mode on or off for main log
	'server': { # Options related to the listening server
		'verbose': False, # Verbose mode on or off for server log
		'address': 'localhost', # Address to listen on. Use an empty string to listen on all interfaces (not recommended)
		'port': 9010, # Port to listen on
		'reverseProxy': None, # If fetchy is meant to be used as a reverse proxy, this should contain the hostname:portNumber of the actual web server behind it.
		'timeout': 5.0, # Timeout to wait for client uploading data to proxy (seconds)
		'chunkSize': 16384, # Chunk size to use when transmitting data back to client
		'bufferSize': 1024, # Buffer size for server forwarding data to client (bytes)
	},
	'client': { # Options related to the HTTP client
		'verbose': False, # Verbose mode on or off for client log
		'userAgent': 'Mozilla/5.0 (Ubuntu; X11; Linux x86_64; rv:8.0) Gecko/20100101 Firefox/8.0', # User-Agent header to use when requesting content from other web servers
		'timeout': 5.0, # Timeout for outgoing HTTP requests (seconds)
		'bufferSize': 16384, # Buffer size for client HTTP requests (bytes)
	},
	'cache': { # Options related to the cache
		'verbose': False, # Verbose mode on or off for cache log
		'gzipCompression': 9, # Strength of gzip compression for cached files (from 0 (don't use compression) to 9 (best compression))
		'gzipMinSize': 128, # Minimum size (in bytes) for gzip compression to be valuable
		'gzipMaxSize': 128 * 1024 * 1024, # Maximum size (in bytes) after which gzip compression becomes too expensive (large files are likely to be in a compressed format already)
		'diskCacheSize': 128 * 1024 * 1024, # Disk cache size (bytes)
		'memoryCacheSize': 32 * 1024 * 1024, # Memory cache size (bytes)
		'directory': '%tmp%/fetchy', # Location of the disk cache ("%tmp%" will be replaced by the system's temporary directory)
		'bufferSize': 32768, # Buffer size for cache I/O operations
	},
	'mini': { # Minification parameters
		'verbose': False, # Verbose mode on or off for mini log
		'js': { # Javascript minification parameters
			'enabled': False, # Enable JS modifications or not
			'closureLevel': 'SIMPLE_OPTIMIZATIONS' # Closure compiler optimization level (None to disable, or one of WHITESPACE_ONLY, SIMPLE_OPTIMIZATIONS, ADVANCED_OPTIMIZATIONS)
		},
		'css': { # CSS minification parameters
			'enabled': True # Enable CSS modifications or not
		},
		'html': { # HTML minification parameters
			'enabled': True, # Enable HTML modifications or not
			'hardcore': True # Try hard to minimize the HTML size
		},
		'images': { # Image minification parameters
			'png': { # PNG minification parameters
				'pngoutStrategy': 2, # PNGOUT strategy (None to disable, or from 0 (slowest, very compressed) to 3 (fastest, not very compressed))
				'bufferSize': 16384 # Buffer size to use when communicating with the pngout process
			},
			'jpeg': { # JPEG minification parameters
				'useJpegtran': True, # True to optimize JPEGs with jpegtran, False to let them be
				'bufferSize': 16384 # Buffer size to use when communicating with the jpegtran process
			},
			'bmp': { # BMP minification parameters
				'enabled': True # True to convert bitmaps to PNG, False to let them be
			},
			'tga': { # TGA minification parameters
				'enabled': True # True to convert Targas to PNG, False to let them be
			}
		}
	}
}
