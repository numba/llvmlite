#!/usr/bin/env python
"""
Build script for the shared library providing the C ABI bridge to LLVM.
"""

from __future__ import print_function

import os
import subprocess
import shutil
import sys
import tempfile


here_dir = os.path.abspath(os.path.dirname(__file__))
build_dir = os.path.join(here_dir, 'build')
target_dir = os.path.join(os.path.dirname(here_dir), 'llvmlite', 'binding')

is_64bit = sys.maxsize >= 2**32


def try_cmake(cmake_dir, build_dir, generator):
    old_dir = os.getcwd()
    try:
        os.chdir(build_dir)
        subprocess.check_call(['cmake', '-G', generator, cmake_dir])
    finally:
        os.chdir(old_dir)


def find_win32_generator():
    """
    Find a suitable cmake "generator" under Windows.
    """
    # XXX this assumes we will find a generator that's the same, or
    # compatible with, the one which was used to compile LLVM... cmake
    # seems a bit lacking here.
    cmake_dir = os.path.join(here_dir, 'dummy')
    # LLVM 3.5 needs VS 2012 minimum.
    for generator in ['Visual Studio 12 2013',
                      'Visual Studio 11 2012']:
        if is_64bit:
            generator += ' Win64'
        build_dir = tempfile.mkdtemp()
        print("Trying generator %r" % (generator,))
        try:
            try_cmake(cmake_dir, build_dir, generator)
        except subprocess.CalledProcessError:
            continue
        else:
            # Success
            return generator
        finally:
            shutil.rmtree(build_dir)
    raise RuntimeError("No compatible cmake generator installed on this machine")


def main_win32():
    generator = find_win32_generator()
    config = 'Release'
    if not os.path.exists(build_dir):
        os.mkdir(build_dir)
    try_cmake(here_dir, build_dir, generator)
    subprocess.check_call(['cmake', '--build', build_dir, '--config', config])
    shutil.copy(os.path.join(build_dir, config, 'llvmlite.dll'), target_dir)


def main_posix(kind, library_ext, default_llvm_config='llvm-config'):
    os.chdir(here_dir)
    makefile = "Makefile.%s" % (kind,)
    llvm_config = os.environ.get('LLVM_CONFIG', default_llvm_config)
    subprocess.check_call(['make', '-f', makefile,
                           'LLVM_CONFIG=%s' % llvm_config])
    shutil.copy('libllvmlite' + library_ext, target_dir)


def main():
    if sys.platform == 'win32':
        main_win32()
    elif sys.platform.startswith('linux'):
        main_posix('linux', '.so')
    elif sys.platform == 'darwin':
        main_posix('osx', '.dylib',
                   default_llvm_config='/usr/local/opt/llvm/bin/llvm-config')
    else:
        raise RuntimeError("unsupported platform: %r" % (sys.platform,))


if __name__ == "__main__":
    main()
