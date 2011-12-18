import os, sys
from utils import *

def which(binary):
	path = u(os.environ.get('PATH', '')).split(u(os.pathsep))
	if sys.platform == 'win32':
		binary += u'.exe'
	for d in path:
		f = os.path.join(d, binary)
		if os.path.isfile(f):
			return f
	return None
