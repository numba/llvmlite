=================
Linking with LLD
=================

.. currentmodule:: llvmlite.binding

The LLD linker is automatically built into llvmlite to provide easy-to-use, cross-platform linking.

Known limitations
==================

Currently, only ``lld::elf::link`` is used and thus COFF and MACHO object files will **not** link.

The following llvm drivers are usable from :func:`lld_main`

* ld.lld   (Linux)
* ld64.lld (macos/darwin)
* lld-link (windows)
* wasm-ld  (Web Assembly)

Functions
==========

* .. function:: lld_main(args)

    * ``args`` is a list of strings passed to the lld linker as arguments
    * returns the output of the specific lld command being run. If there is an error, an :exc:`Exception` will be thrown.

    example: ``binding.lld_main(["ld.lld", "--help"])``


* .. function:: lld_linux(output_file, objects, args=[])

    * ``objects`` is a list of object files' names as **strings**.
    * ``args`` is a list of strings passed to the lld linker as arguments (at the end of the command)
    * returns the output of lld_main for the given arguments

    Links given object files into an executable using :func:`lld_main()`


* .. function:: lld_windows(output_file, objects, args=[])

    Link for Windows target


* .. function:: lld_macos(output_file, objects, args=[])

    Link for Macos target


* .. function:: lld_wasm(output_file, objects, args=[])

    Link for wasm target


* .. function:: lld_auto(output_file, objects, args=[], add_extension=True)
    
    * ``add_extension`` should this function automatically add **.exe** and **.app** for windows and macos targets
    * returns the output of lld_main for the given arguments

    Automatically determines which function to use given the host operating system.
    This will only use the ``lld_linux``, ``lld_windows``, and ``lld_macos`` functions.
    Throws :exc:`Exception` if the host operating system isn't ``Darwin``, ``Windows``, or ``Linux``