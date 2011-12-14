# Default fetchy settings
config = {
	'verbose': False, # Verbose mode on or off
	'port': 9010,
	'quiet': False, # True to make the process completely quiet
	'httpTimeout': 5.0, # Timeout for outgoing HTTP requests (seconds)
	'diskCacheSize': 128 * 1024 * 1024, # Disk cache size (bytes)
	'clientBufferSize': 16384, # Buffer size for client HTTP requests (bytes)
	'serverBufferSize': 16384, # Buffer size for server forwarding data to client (bytes)
}
