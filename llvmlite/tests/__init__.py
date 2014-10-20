
import sys

if sys.version_info <= (2, 6):
    # Monkey-patch unittest2 into the import machinery, so that
    # submodule imports work properly too.
    import unittest2
    sys.modules['unittest'] = unittest2

from unittest import *

try:
    import faulthandler
except ImportError:
    pass
else:
    try:
        # May fail in IPython Notebook with UnsupportedOperation
        faulthandler.enable()
    except BaseException as e:
        msg = "Failed to enable faulthandler due to:\n{err}"
        warnings.warn(msg.format(err=e))
