from __future__ import absolute_import

import sys

# Inject enum module backport if necessary
try:
    import enum
except ImportError:
    from . import enum
    sys.modules['enum'] = enum
del enum
