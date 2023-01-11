from ctypes import c_bool, c_uint, POINTER, c_char_p, c_int, c_wchar_p
import platform

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
    args = (c_char_p*len(lld_args))()
    for i, arg in enumerate(lld_args):
        args[i] = arg.encode()
    with  ffi.OutputString() as outstr:
        r = ffi.lib.lld_main(len(lld_args), args, outstr)
        if r != False:
            raise Exception("lld_main() failed, error code: %d" % r)
        
        return str(outstr)

def lld_windows(output: str, objects: list[str], args: list[str] = []) -> str:
    '''
    runs the command `lld-link -o {output-file} {*input_files} {*args}`
    output: output as a str
    object: a list of input .o files as strings
    args: additional arguments for the command
    '''
    return lld_main(["lld-link", "-o", output, *objects, *args])

def lld_macos(output: str, objects: list[str], args: list[str] = []) -> str:
    '''
    runs the command `ld64.lld -o {output-file} {*input_files} {*args}`
    output: output as a str
    object: a list of input .o files as strings
    args: additional arguments for the command
    '''
    return lld_main(["ld64.lld", "-o", output, *objects, *args])

def lld_linux(output: str, objects: list[str], args: list[str] = []) -> str:
    '''
    runs the command `ld.lld -o {output-file} {*input_files} {*args}`
    output: output as a str
    object: a list of input .o files as strings
    args: additional arguments for the command
    '''
    return lld_main(["ld.lld", "-o", output, *objects, *args])

def lld_wasm(output: str, objects: list[str], args: list[str] = []) -> str:
    '''
    runs the command `ld.lld -o {output-file} {*input_files} {*args}`
    output: output as a str
    object: a list of input .o files as strings
    args: additional arguments for the command
    '''
    return lld_main(["wasm-ld", "-o", output, *objects, *args])

def lld_auto(output: str, objects: list[str], args: list[str] = [], add_extension = True) -> str:
    '''
    Automatically determines which lld function to run based on the hosts system.
    Does not use `lld_wasm()`

    add_extension: adds `.exe` and other file endings automatically 
    '''
    system = platform.system()

    if system in "Linux":
        return lld_linux(output, objects, args)
    if system == "Windows":
        name = output+('.exe'*add_extension)
        return lld_windows(name, objects, args)
    if system == "Darwin": # Macos
        name = output+('.app'*add_extension)
        return lld_macos(name, objects, args)