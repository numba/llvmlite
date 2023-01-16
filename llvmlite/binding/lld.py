from ctypes import c_bool, POINTER, c_char_p, c_int
import platform
from typing import List

from llvmlite.binding import ffi


ffi.lib.lld_main.restype = c_bool
ffi.lib.lld_main.argtypes = [c_int, POINTER(c_char_p), POINTER(c_char_p)]


def lld_main(lld_args) -> str:
    """
    Calls LLD - the LLVM linker.

    The function calls the `lld::elf::link()` with the `lld_args` (list of
    strings) as arguments.

    Examples
    ~~~~~~~~

    Shows help:

    >>> from llvmlite.binding import lld_main
    >>> lld_main(["ld.lld", "--help"])
    """
    args = (c_char_p * len(lld_args))()
    for i, arg in enumerate(lld_args):
        args[i] = arg.encode()
    with ffi.OutputString() as outstr:
        r = ffi.lib.lld_main(len(lld_args), args, outstr)
        if r:
            raise Exception("lld_main() failed, error code: %d\
                            \nCommand Output: %s" % (r, str(outstr)))
        return str(outstr)


def lld_runner(command: str):
    def wrapped(output: str, objects: List[str], args: List[str] = []) -> str:
        '''
        runs the command:
        "{platform's lld command} -o {output-file} {*input_files} {*args}"
        output: output file as a str
        object: a list of input .o files as strings
        args: additional arguments for the command
        '''
        return lld_main([command, '-o', output, *objects, *args])
    return wrapped


lld_windows = lld_runner("lld-link")
lld_macos = lld_runner("ld64.lld")
lld_linux = lld_runner("ld.lld")
lld_wasm = lld_runner("wasm-ld")


def lld_auto(output: str, objects: list[str],
             args: list[str] = [],
             add_extension=True) -> str:
    '''
    Automatically determines which lld function
    to run based on the hosts system.

    Does not use `lld_wasm()`

    add_extension: adds `.exe` and other file endings automatically
    '''
    system = platform.system()

    if system == "Linux":
        # has no standard file extension
        return lld_linux(output, objects, args)
    elif system == "Windows":
        name = output + ('.exe' * add_extension)
        return lld_windows(name, objects, args)
    elif system == "Darwin": # Macos
        name = output + ('.app' * add_extension)
        return lld_macos(name, objects, args)
    else:
        msg = (f'''Invalid host system name: {system}
                If you are sure a driver exists for this system,
                please use the `lld_main()` function
                '''.strip())
        raise RuntimeError(msg)
