import re
from converter import buildConverter

_bmpRegex = re.compile(u'.bmp$', re.IGNORECASE)
bmpConverter = buildConverter('BMP', lambda x : _bmpRegex.sub('.png', x))

process = bmpConverter.process
init = bmpConverter.init
