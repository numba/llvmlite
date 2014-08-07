from __future__ import print_function, absolute_import
try:
    from StringIO import StringIO as _StringIO

    class StringIO(_StringIO):
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()

except ImportError:
    from io import StringIO


class DuplicatedNameError(NameError):
    pass


class NameScope(object):
    def __init__(self, parent=None):
        self.parent = parent
        self._useset = set([''])
        self._basenamemap = {}

    def is_used(self, name):
        if name in self._useset:
            return True
        elif self.parent and self.parent.is_used(name):
            return True
        else:
            return False

    def register(self, name):
        assert name, "name is empty"
        if self.is_used(name):
            raise DuplicatedNameError(name)

        self._useset.add(name)

    def deduplicate(self, name):
        basename = name
        while self.is_used(name):
            ident = self._basenamemap.get(basename, 1)
            self._basenamemap[basename] = ident + 1
            name = "%s.%u" % (basename, ident)
        return name

    def get_child(self):
        return type(self)(parent=self)
