"""
A collection of analysis utils
"""

from __future__ import absolute_import, print_function

import re
from collections import defaultdict, Mapping, Sequence
from ctypes import POINTER, c_char_p, c_int

from llvmlite import ir
from . import ffi
from .module import parse_assembly


def get_function_cfg(func, show_inst=True):
    """Return a string of the control-flow graph of the function in DOT
    format. If the input `func` is not a materialized function, the module
    containing the function is parsed to create an actual LLVM module.
    The `show_inst` flag controls whether the instructions of each block
    are printed.
    """
    assert func is not None
    if isinstance(func, ir.Function):
        mod = parse_assembly(str(func.module))
        func = mod.get_function(func.name)

    # Assume func is a materialized function
    with ffi.OutputString() as dotstr:
        ffi.lib.LLVMPY_WriteCFG(func, dotstr, show_inst)
        return str(dotstr)


def view_dot_graph(graph, filename=None, view=False):
    """
    View the given DOT source.  If view is True, the image is rendered
    and viewed by the default application in the system.  The file path of
    the output is returned.  If view is False, a graphviz.Source object is
    returned.  If view is False and the environment is in a IPython session,
    an IPython image object is returned and can be displayed inline in the
    notebook.

    This function requires the graphviz package.

    Args
    ----
    - graph [str]: a DOT source code
    - filename [str]: optional.  if given and view is True, this specifies
                      the file path for the rendered output to write to.
    - view [bool]: if True, opens the rendered output file.

    """
    # Optionally depends on graphviz package
    import graphviz as gv

    src = gv.Source(graph)
    if view:
        # Returns the output file path
        return src.render(filename, view=view)
    else:
        # Attempts to show the graph in IPython notebook
        try:
            import IPython.display as display
        except ImportError:
            return src
        else:
            format = 'svg'
            return display.SVG(data=src.pipe(format))


def control_structures_analysis(func):
    assert func is not None
    if isinstance(func, ir.Function):
        mod = parse_assembly(str(func.module))
        func = mod.get_function(func.name)

    assert func.type.is_function_pointer
    with ffi.OutputString() as output:
        ffi.lib.LLVMPY_RunControlStructuresAnalysis(func, output)
        return ControlStructures(func, str(output))


def _cached_property(key):
    def wrap(compute_fn):
        @property
        def output(self):
            ret = self._output.get(key)
            if ret is None:
                self._output[key] = ret = compute_fn(self)
            return ret

        return output

    return wrap


class ImmutableMapping(Mapping):
    def __init__(self, dct):
        self._dct = dct

    def __iter__(self):
        return iter(self._dct)

    def __len__(self):
        return len(self._dct)

    def __getitem__(self, item):
        return self._dct[item]

    def __str__(self):
        return str(self._dct)

    def __repr__(self):
        return repr(self._dct)


class ImmutableSequence(Sequence):
    def __init__(self, seq):
        self._seq = seq

    def __getitem__(self, item):
        return self._seq[item]

    def __len__(self):
        return len(self._seq)

    def __str__(self):
        return str(self._seq)

    def __repr__(self):
        return repr(self._seq)


class ControlStructures(object):
    """
    This class provides a lazy parser for the text description from the
    result of the `control_structures_analysis()` function.

    Access to the result of each analysis pass is provided from attributes:
    e.g. region_info, post_dominators, etc..  The information is parsed
    lazily and structures are constructed to facilitate the use of the analysis
    result.

    """

    def __init__(self, func, descr):
        self._function = func
        self._bbmap = {}
        bb = self._function.entry_basic_block
        while True:
            self._bbmap[bb.name] = bb
            try:
                bb = bb.next
            except ValueError:
                break

        self._sections = self._split_sections(descr)
        self._output = {}

    @_cached_property('regions')
    def region_info(self):
        """
        Returns the root (toplevel region) of the region tree.
        """
        return self._parse_regions()

    @_cached_property('postdoms')
    def post_dominators(self):
        """
        Returns a dictionary of the post-dominators as a mapping from a block
        to its immediate post-dominator.
        """
        return ImmutableMapping(self._parse_postdoms())

    @_cached_property('doms')
    def dominators(self):
        """
        Returns a dictionary of the dominators as a mapping from a block
        to its immediate dominators.
        """
        return ImmutableMapping(self._parse_doms())

    @_cached_property('domfront')
    def dominance_frontiers(self):
        """
        Returns a dictionary of the dominance frontiers as a mapping from
        a block to its dominance frontiers.
        """
        return ImmutableMapping(self._parse_domfront())

    @_cached_property('loops')
    def loops(self):
        """
        Returns a list of loop information.
        """
        return ImmutableSequence(self._parse_loops())

    def _split_sections(self, descr):
        """
        Internal function for splitting the descriptor text into different
        sections.
        """
        prefix_template = '>>> {0}\n'
        sections = ['regions', 'postdoms', 'domfront', 'doms', 'loops']
        starts = []
        stops = []
        lastpos = 0
        sectmap = {}
        for sect in sections:
            prefix = prefix_template.format(sect)
            lastpos = descr.index(prefix, lastpos)
            starts.append(lastpos + len(prefix))
            stops.append(lastpos)

        stops.append(len(descr))
        for start, stop, sect in zip(starts, stops[1:], sections):
            sectmap[sect] = descr[start:stop]
        return sectmap

    def _parse_regions(self):
        desc = self._sections['regions']

        regionmap = {}

        # Parse each line from the region description output
        # Format: <BB name>|<Region name>|<List of Region parents...>
        for line in desc.splitlines():
            if '|' not in line:
                break
            elems = line.split('|')
            bb = elems[0].strip()
            regname = elems[1].strip()
            parents = elems[2:]

            if regname not in regionmap:
                regionmap[regname] = Region(regname)

            cur = regionmap[regname]
            cur.blocks.add(self._bbmap[bb])

            # Assign parent relationship
            for par in parents:
                par = par.strip()
                if par not in regionmap:
                    regionmap[par] = Region(par)
                parent = regionmap[par]
                parent.subregions.add(cur)
                cur = parent

        toplvl = line.strip()
        # Toplevel region must be defined already
        return regionmap[toplvl]

    _regex_postdom = re.compile(r"^\s*\[(\d)\]\s+(.*)\s\{.*\}$")

    def _parse_trees(self, desc):
        tree = {}
        stack = []
        # Make a dummy object as the sentinel
        sentinel = object()
        for m in _yield_matches(desc.splitlines(), self._regex_postdom):
            grps = m.groups()
            depth = int(grps[0])
            nodename = grps[1]
            if nodename.startswith('%'):
                bb = self._bbmap[nodename[1:]]

                assert depth > 0
                if depth == 1:
                    stack = [bb]
                else:
                    stack = stack[:depth - 1]
                    parent = stack[-1]
                    if parent is not sentinel:
                        tree[bb] = parent
                    stack.append(bb)

                    assert depth == len(stack)
            elif nodename == '<<exit node>>':
                stack.append(sentinel)
            else:
                raise ValueError("unknown format: nodename={0!r}".format(
                    nodename))

        return tree

    def _parse_postdoms(self):
        desc = self._sections['postdoms']
        return self._parse_trees(desc)

    def _parse_doms(self):
        desc = self._sections['doms']
        return self._parse_trees(desc)

    _regex_domfront = re.compile(r"^\s*DomFrontier for BB %(.*) is:(.*)$")

    def _parse_domfront(self):
        desc = self._sections['domfront']
        domfront = {}

        for m in _yield_matches(desc.splitlines(), self._regex_domfront):
            grps = m.groups()
            src, dst = grps
            bblist = dst.strip().split()
            domfront[self._bbmap[src]] = frozenset(self._bbmap[bb.lstrip('%')]
                                                   for bb in bblist)

        return domfront

    _regex_loops = re.compile(r"^Loop at depth (\d) containing: (.*)$")

    def _parse_loops(self):
        desc = self._sections['loops']
        loops = []

        for m in _yield_matches(desc.splitlines(), self._regex_loops):
            depth = int(m.group(1))
            info = m.group(2)
            loop = Loop(depth=depth)
            # parse info
            for sect in info.split(','):

                has_tags = set()
                for tag in Loop.TAGS:
                    tagfmt = '<{0}>'.format(tag)
                    if tagfmt in sect:
                        has_tags.add(tag)

                # strip tags
                if has_tags:
                    sect = sect[:sect.index('<')]
                bb = self._bbmap[sect.lstrip('%')]

                # add block
                loop.blocks.add(bb)
                # add tags
                for tag in has_tags:
                    loop._tag_block(bb, tag)

            loop.verify()
            loops.append(loop)

        return loops


class Loop(object):
    TAGS = frozenset(['header', 'latch', 'exiting'])

    def __init__(self, depth):
        self.depth = depth
        self.blocks = set()
        self._tags = defaultdict(set)
        self._header = None
        self._exits = set()
        self._latches = set()
        self._tagless = None

    def _tag_block(self, blk, tag):
        assert tag in self.TAGS
        self.blocks.add(blk)
        self._tags[blk].add(tag)
        if tag == 'header':
            assert self._header is None
            self._header = blk
        elif tag == 'latch':
            self._latches.add(blk)
        elif tag == 'exiting':
            self._exits.add(blk)

    def tags(self, blk):
        """
        Returns the tags as a set for the given block
        or raises ValueError if it does not belong to this loop
        """
        if blk not in self.blocks:
            raise ValueError("{0} does not belong to this loop".format(
                blk.name))
        return self._tags[blk]

    @property
    def header(self):
        """
        The start of the loop.
        """
        ret = self._header
        assert ret is not None
        return ret

    @property
    def exits(self):
        """
        The exit points of the loop.  An exit ends with the branch that
        goes to the header (an exit can be a latch) or a latch, or escape the
        cyclic code.
        """
        return self._exits

    @property
    def latches(self):
        """Latches branch back to the loop header.
        """
        return frozenset(self._latches)

    @property
    def tagless(self):
        """
        Other basic blocks in the loop that is not tagged.
        """
        if not self._tagless:
            self._tagless = frozenset(bb for bb in self.blocks
                                      if not self.tags(bb))
        return self._tagless

    def verify(self):
        """
        Verify self structure. Raise ValueError on failure.
        """
        combined = set([self.header]) | self.tagless | self.latches | self.exits
        if self.blocks != combined:
            raise ValueError("malformed")

    def __str__(self):
        def fmt(inner, bb):
            tags = ','.join([str(t) for t in self.tags(bb)])
            if tags:
                inner.append("{0} [{1}]".format(bb.name, tags))
            else:
                inner.append("{0}".format(bb.name))

        showed = set()
        inner = []
        fmt(inner, self.header)
        showed.add(self.header)
        for bb in (self.exits - showed):
            fmt(inner, bb)
        showed |= self.exits
        for bb in (self.latches - showed):
            fmt(inner, bb)
        for bb in self.tagless:
            fmt(inner, bb)

        return "Loop: " + '; '.join(inner)


class Region(object):
    """
    Represent a single-entry single-exit region as defined in the
    Program Structure Tree paper by Johnson, Pearson and Pingali.

    The `blocks` attribute is a set of basic blocks that is directly in the
    region, without including any basic blocks in the subregion.
    The `subregions` attribute is a set of all inner regions.
    """

    def __init__(self, name):
        self.name = name
        self.blocks = set()
        self.subregions = set()

    @property
    def contained_blocks(self):
        """
        Returns all contained blocks
        """
        ret = set(self.blocks)
        for sub in self.subregions:
            ret |= sub.contained_blocks
        return ret

    def __iter__(self):
        # Iterate over all contained blocks with no specific order
        def iterator():
            # Yield all directly contained block
            for i in self.blocks:
                yield i
            # Yield all sub region blocks
            for sub in self.subregions:
                for j in sub:
                    yield j

        return iterator()

    def __contains__(self, bb):
        return bb in self.blocks or any(bb in sub for sub in self.subregions)

    def __repr__(self):
        return "<RegionTree {0!r}>".format(self.name)

    def __str__(self):
        buf = []
        self._format(buf)
        return '\n'.join(buf)

    def _format(self, buf, depth=0):
        """
        Format the region tree into a list buffer (`buf`).
        """
        indent = '  ' * depth
        bbnames = [repr(bb.name) for bb in self.blocks]
        buf.append("{0}Region {1} : {2}".format(indent, self.name,
                                                ', '.join(bbnames)))
        # Recursively format sub regions
        for sub in self.subregions:
            sub._format(buf, depth=depth + 1)


def _yield_matches(lines, regex):
    """
    Skip until a match and continues to yield each matches line until the first
    mismatch.
    """
    lniter = iter(lines)
    for ln in lniter:
        m = regex.match(ln)
        if not m:
            continue
        else:
            yield m
            break
    for ln in lniter:
        m = regex.match(ln)
        if not m:
            break
        yield m


# Ctypes binding
ffi.lib.LLVMPY_WriteCFG.argtypes = [ffi.LLVMValueRef, POINTER(c_char_p), c_int]

ffi.lib.LLVMPY_RunControlStructuresAnalysis.argtypes = [ffi.LLVMValueRef,
                                                        POINTER(c_char_p)]
