
import sys


if sys.version_info < (3, 0):
    def _decode_string(b):
        return b
else:
    def _decode_string(b):
        return b.decode('utf-8')
