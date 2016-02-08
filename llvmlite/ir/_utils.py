from __future__ import print_function, absolute_import

from collections import defaultdict


class DuplicatedNameError(NameError):
    pass


class NameScope(object):
    def __init__(self, parent=None):
        self.parent = parent
        self._useset = set([''])
        self._basenamemap = defaultdict(int)

    def is_used(self, name):
        scope = self
        while scope is not None:
            if name in scope._useset:
                return True
            scope = scope.parent
        return False

    def register(self, name, deduplicate=False):
        if deduplicate:
            name = self.deduplicate(name)
        elif self.is_used(name):
            raise DuplicatedNameError(name)
        self._useset.add(name)
        return name

    def deduplicate(self, name):
        basename = name
        while self.is_used(name):
            ident = self._basenamemap[basename] + 1
            self._basenamemap[basename] = ident
            name = "{0}.{1}".format(basename, ident)
        return name

    def get_child(self):
        return type(self)(parent=self)


class _StrCaching(object):

    def __str__(self):
        try:
            return self.__cached_str
        except AttributeError:
            s = self.__cached_str = self._to_string()
            return s


class _StringReferenceCaching(object):

    def get_reference(self):
        try:
            return self.__cached_refstr
        except AttributeError:
            s = self.__cached_refstr = self._get_reference()
            return s
