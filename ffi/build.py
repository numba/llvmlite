#!/usr/bin/env python
"""
Build script for the shared library providing the C ABI bridge to LLVM.
"""

import os
import subprocess
import shutil
import sys


here_dir = os.path.abspath(os.path.dirname(__file__))
build_dir = os.path.join(here_dir, 'build')
target_dir = os.path.join(os.path.dirname(here_dir), 'llvmlite', 'binding')

is_64bit = sys.maxsize >= 2**32


def main_win32():
    # XXX: It would be nice if we could choose the generator's bitness
    # (32/64) without hardcoding its full name...
    config = 'Release'
    generator = 'Visual Studio 11 2012'
    if is_64bit:
        generator += ' Win64'
    if not os.path.isdir(build_dir):
        os.mkdir(build_dir)
    os.chdir(build_dir)
    subprocess.check_call(['cmake', '-G', generator, here_dir])
    subprocess.check_call(['cmake', '--build', '.', '--config', config])
    shutil.copy(os.path.join(build_dir, config, 'llvmlite.dll'), target_dir)


def main_posix(kind, library_ext):
    os.chdir(here_dir)
    makefile = "Makefile.%s" % (kind,)
    subprocess.check_call(['make', '-f', makefile])
    shutil.copy('libllvmlite' + library_ext, target_dir)


def main():
    if sys.platform == 'win32':
        main_win32()
    elif sys.platform.startswith('linux'):
        main_posix('linux', '.so')
    elif sys.platform == 'darwin':
        main_posix('osx', '.dylib')
    else:
        raise RuntimeError("unsupported platform: %r" % (sys.platform,))


if __name__ == "__main__":
    main()
