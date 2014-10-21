
import sys


if sys.version_info < (3, 0):
    def _encode_string(s):
        if isinstance(s, bytes):
            return s
        else:
            return s.encode('utf-8')

    def _decode_string(b):
        return b
else:
    def _encode_string(s):
        return s.encode('utf-8')

    def _decode_string(b):
        return b.decode('utf-8')

_encode_string.__doc__ = """Encode a string for use by LLVM."""
_decode_string.__doc__ = """Decode a LLVM character (byte)string."""
