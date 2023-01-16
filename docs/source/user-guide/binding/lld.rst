=================
Linking with LLD
=================

.. currentmodule:: llvmlite.binding

The LLD linker is automatically built into llvmlite to provide easy-to-use, cross-platform linking.

Known limitations
==================

Currently, only ``lld::elf::link`` is used and thus COFF and MACHO object files will **not** link.

The following llvm drivers are usable from :function:`lld_main`

* ld.lld   (Linux)
* ld64.lld (macos/darwin)
* lld-link (windows)
* wasm-ld  (Web Assembly)

Functions
==========

* .. function:: lld_main(args)

    * ``args`` is a list of strings passed to the lld linker as arguments
    * returns the output of the specific lld command being run. If there is an error, an ``Exception`` will be thrown.

    example: ``binding.lld_main(["ld.lld", "--help"])``


* .. function:: lld_linux(ouput, objects, args=[])

    * ``output`` is the name of the output file as a **string**
    * ``objects`` is a list of object files' names as **strings**.
    * ``args`` is a list of strings passed to the lld linker as arguments (at the end of the command)
    * returns the output of lld_main for the given arguments

    Links given object files into an executable using ``lld_main()``


* .. function:: lld_windows(ouput, objects, args=[])

    * ``output`` is the name of the output file as a **string**
    * ``objects`` is a list of object files' names as **strings**.
    * ``args`` is a list of strings passed to the lld linker as arguments (at the end of the command)
    * returns the output of lld_main for the given arguments

    Links given object files into an executable using ``lld_main()``


* .. function:: lld_macos(ouput, objects, args=[])

    * ``output`` is the name of the output file as a **string**
    * ``objects`` is a list of object files' names as **strings**.
    * ``args`` is a list of strings passed to the lld linker as arguments (at the end of the command)
    * returns the output of lld_main for the given arguments

    Links given object files into an executable using ``lld_main()``


* .. function:: lld_wasm(ouput, objects, args=[])

    * ``output`` is the name of the output file as a **string**
    * ``objects`` is a list of object files' names as **strings**.
    * ``args`` is a list of strings passed to the lld linker as arguments (at the end of the command)
    * returns the output of lld_main for the given arguments

    Links given object files into an executable using ``lld_main()``


* .. function:: lld_auto(ouput, objects, args=[], add_extension=True)

    * ``output`` is the name of the output file as a **string**
    * ``objects`` is a list of object files' names as **strings**.
    * ``args`` is a list of strings passed to the lld linker as arguments (at the end of the command)
    * ``add_extension`` should this function automatically add **.exe** and **.app** for windows and macos targets
    * returns the output of lld_main for the given arguments

    Automatically determines which function to use given the host operating system.
    This will only use the ``lld_linux``, ``lld_windows``, and ``lld_macos`` functions.
    Creates and exception if the host operating system isn't ``Darwin``, ``Windows``, or ``Linux``