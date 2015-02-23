from __future__ import absolute_import

try:
    import enum
except ImportError:
    raise ImportError("could not find the 'enum' module; please install "
                      "it using e.g. 'pip install enum34'")

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
