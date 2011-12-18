import re
from converter import buildConverter

_tgaRegex = re.compile(u'.tga$', re.IGNORECASE)
_tgaConverter = buildConverter('TGA', lambda x : _tgaRegex.sub('.tga', x))

process = _tgaConverter.process
init = _tgaConverter.init
