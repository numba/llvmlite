from __future__ import annotations

from collections import defaultdict
from typing import Any


class DuplicatedNameError(NameError):
    pass


class NameScope(object):
    def __init__(self) -> None:
        self._useset: set[str] = set([''])
        self._basenamemap: defaultdict[str, int] = defaultdict(int)

    def is_used(self, name: str) -> bool:
        return name in self._useset

    def register(self, name: str, deduplicate: bool = False) -> str:
        if deduplicate:
            name = self.deduplicate(name)
        elif self.is_used(name):
            raise DuplicatedNameError(name)
        self._useset.add(name)
        return name

    def deduplicate(self, name: str) -> str:
        basename = name
        while self.is_used(name):
            ident = self._basenamemap[basename] + 1
            self._basenamemap[basename] = ident
            name = "{0}.{1}".format(basename, ident)
        return name

    def get_child(self) -> Any:
        # FIXME: which types can this produce??
        return type(self)(parent=self)  # type: ignore


class _StrCaching:
    # FIXME: self.__cached_str missing
    # FIXME: self.to_string() missing

    def _clear_string_cache(self) -> None:
        try:
            del self.__cached_str  # type: ignore
        except AttributeError:
            pass

    def __str__(self) -> str:
        try:
            return self.__cached_str  # type: ignore
        except AttributeError:
            s = self.__cached_str = self._to_string()  # type: ignore
            return s  # type: ignore


class _StringReferenceCaching:
    # FIXME: self.__cached_refstr missing
    # FIXME: self._get_reference missing

    def get_reference(self) -> str:
        try:
            return self.__cached_refstr  # type: ignore
        except AttributeError:
            s = self.__cached_refstr = self._get_reference()  # type: ignore
            return s  # type: ignore


class _HasMetadata:
    # FIXME: self.metadata missing

    def set_metadata(self, name: str, node: Any) -> None:
        """
        Attach unnamed metadata *node* to the metadata slot *name* of this
        value.
        """
        self.metadata[name] = node  # type: ignore

    def _stringify_metadata(self, leading_comma: bool = False) -> str:
        if self.metadata:  # type: ignore
            buf: list[str] = []
            if leading_comma:
                buf.append("")
            buf += ["!{0} {1}".format(k, v.get_reference())
                    for k, v in self.metadata.items()]  # type: ignore
            return ', '.join(buf)
        else:
            return ''
