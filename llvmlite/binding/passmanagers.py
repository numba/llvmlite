from ctypes import (c_bool, c_char_p, c_int, c_size_t, Structure, byref,
                    POINTER)
from collections import namedtuple
from enum import IntFlag
from llvmlite.binding import ffi
from llvmlite.binding.initfini import llvm_version_info
import os
from tempfile import mkstemp
from llvmlite.binding.common import _encode_string

llvm_version_major = llvm_version_info[0]

_prunestats = namedtuple('PruneStats',
                         ('basicblock diamond fanout fanout_raise'))


class PruneStats(_prunestats):
    """ Holds statistics from reference count pruning.
    """

    def __add__(self, other):
        if not isinstance(other, PruneStats):
            msg = 'PruneStats can only be added to another PruneStats, got {}.'
            raise TypeError(msg.format(type(other)))
        return PruneStats(self.basicblock + other.basicblock,
                          self.diamond + other.diamond,
                          self.fanout + other.fanout,
                          self.fanout_raise + other.fanout_raise)

    def __sub__(self, other):
        if not isinstance(other, PruneStats):
            msg = ('PruneStats can only be subtracted from another PruneStats, '
                   'got {}.')
            raise TypeError(msg.format(type(other)))
        return PruneStats(self.basicblock - other.basicblock,
                          self.diamond - other.diamond,
                          self.fanout - other.fanout,
                          self.fanout_raise - other.fanout_raise)


class _c_PruneStats(Structure):
    _fields_ = [
        ('basicblock', c_size_t),
        ('diamond', c_size_t),
        ('fanout', c_size_t),
        ('fanout_raise', c_size_t)]


def dump_refprune_stats(printout=False):
    """ Returns a namedtuple containing the current values for the refop pruning
    statistics. If kwarg `printout` is True the stats are printed to stderr,
    default is False.
    """

    stats = _c_PruneStats(0, 0, 0, 0)
    do_print = c_bool(printout)

    ffi.lib.LLVMPY_DumpRefPruneStats(byref(stats), do_print)
    return PruneStats(stats.basicblock, stats.diamond, stats.fanout,
                      stats.fanout_raise)


def set_time_passes(enable):
    """Enable or disable the pass timers.

    Parameters
    ----------
    enable : bool
        Set to True to enable the pass timers.
        Set to False to disable the pass timers.
    """
    ffi.lib.LLVMPY_SetTimePasses(c_bool(enable))


def report_and_reset_timings():
    """Returns the pass timings report and resets the LLVM internal timers.

    Pass timers are enabled by ``set_time_passes()``. If the timers are not
    enabled, this function will return an empty string.

    Returns
    -------
    res : str
        LLVM generated timing report.
    """
    with ffi.OutputString() as buf:
        ffi.lib.LLVMPY_ReportAndResetTimings(buf)
        return str(buf)



class RefPruneSubpasses(IntFlag):
    PER_BB       = 0b0001    # noqa: E221
    DIAMOND      = 0b0010    # noqa: E221
    FANOUT       = 0b0100    # noqa: E221
    FANOUT_RAISE = 0b1000
    ALL = PER_BB | DIAMOND | FANOUT | FANOUT_RAISE




# ============================================================================
# FFI

ffi.lib.LLVMPY_DumpRefPruneStats.argtypes = [POINTER(_c_PruneStats), c_bool]
