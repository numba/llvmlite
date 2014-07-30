from __future__ import print_function, absolute_import


class NameManager(object):
    """Manages symbol naming to avoid duplication.
    Which naming
    """

    def __init__(self):
        self.used = {}

    def deduplicate(self, name):
        if name in self.used:
            ct = self.used[name]
            self.used[name] = ct + 1
            name = '%s.%d' % (name, ct)
        else:
            self.used[name] = 1
            if not name:
                name = '.0'

        return name

    def __contains__(self, name):
        return name in self.used
