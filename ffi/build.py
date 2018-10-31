#!/usr/bin/env python
"""
Build script for the shared library providing the C ABI bridge to LLVM.
"""

from __future__ import print_function

from ctypes.util import find_library
import re
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


def run_llvm_config(llvm_config, args):
    cmd = [llvm_config] + args
    p = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    out = out.decode()
    err = err.decode()
    rc = p.wait()
    if rc != 0:
        raise RuntimeError("Command %s returned with code %d; stderr follows:\n%s\n"
                           % (cmd, rc, err))
    return out


def find_win32_generator():
    """
    Find a suitable cmake "generator" under Windows.
    """
    # XXX this assumes we will find a generator that's the same, or
    # compatible with, the one which was used to compile LLVM... cmake
    # seems a bit lacking here.
    cmake_dir = os.path.join(here_dir, 'dummy')
    # LLVM 4.0+ needs VS 2015 minimum.
    generators = []
    if os.environ.get("CMAKE_GENERATOR"):
        generators.append(os.environ.get("CMAKE_GENERATOR"))

    # Drop generators that are too old
    vspat = re.compile('Visual Studio (\d+)')
    def drop_old_vs(g):
        m = vspat.match(g)
        if m is None:
            return True  # keep those we don't recognize
        ver = int(m.group(1))
        return ver >= 14
    generators = list(filter(drop_old_vs, generators))

    generators.append('Visual Studio 14 2015' + (' Win64' if is_64bit else ''))
    for generator in generators:
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
    # Run configuration step
    try_cmake(here_dir, build_dir, generator)
    subprocess.check_call(['cmake', '--build', build_dir, '--config', config])
    shutil.copy(os.path.join(build_dir, config, 'llvmlite.dll'), target_dir)


def main_posix(kind, library_ext):
    os.chdir(here_dir)
    # Check availability of llvm-config
    llvm_config = os.environ.get('LLVM_CONFIG', 'llvm-config')
    print("LLVM version... ", end='')
    sys.stdout.flush()
    try:
        out = subprocess.check_output([llvm_config, '--version'])
    except (OSError, subprocess.CalledProcessError):
        raise RuntimeError("%s failed executing, please point LLVM_CONFIG "
                           "to the path for llvm-config" % (llvm_config,))

    out = out.decode('latin1')
    print(out)
    if not out.startswith('6.0.'):
        msg = (
            "Building llvmlite requires LLVM 6.0.x. Be sure to "
            "set LLVM_CONFIG to the right executable path.\n"
            "Read the documentation at http://llvmlite.pydata.org/ for more "
            "information about building llvmlite.\n"
            )
        raise RuntimeError(msg)

    # Get LLVM information for building
    libs = run_llvm_config(llvm_config, "--system-libs --libs all".split())
    # Normalize whitespace (trim newlines)
    os.environ['LLVM_LIBS'] = ' '.join(libs.split())

    cxxflags = run_llvm_config(llvm_config, ["--cxxflags"])
    # on OSX cxxflags has null bytes at the end of the string, remove them
    cxxflags = cxxflags.replace('\0', '')
    cxxflags = cxxflags.split() + ['-fno-rtti', '-g']

    # look for SVML
    include_dir = run_llvm_config(llvm_config, ['--includedir']).strip()
    svml_indicator = os.path.join(include_dir, 'llvm', 'IR', 'SVML.gen')
    if os.path.isfile(svml_indicator):
        cxxflags = cxxflags + ['-DHAVE_SVML']
        print('SVML detected')
    else:
        print('SVML not detected')

    os.environ['LLVM_CXXFLAGS'] = ' '.join(cxxflags)

    ldflags = run_llvm_config(llvm_config, ["--ldflags"])
    os.environ['LLVM_LDFLAGS'] = ldflags.strip()
    # static link libstdc++ for portability
    if int(os.environ.get('LLVMLITE_CXX_STATIC_LINK', 0)):
        os.environ['CXX_STATIC_LINK'] = "-static-libstdc++"

    makefile = "Makefile.%s" % (kind,)
    subprocess.check_call(['make', '-f', makefile])
    shutil.copy('libllvmlite' + library_ext, target_dir)


def main():
    if sys.platform == 'win32':
        main_win32()
    elif sys.platform.startswith('linux'):
        main_posix('linux', '.so')
    elif sys.platform.startswith(('freebsd','openbsd')):
        main_posix('freebsd', '.so')
    elif sys.platform == 'darwin':
        main_posix('osx', '.dylib')
    else:
        raise RuntimeError("unsupported platform: %r" % (sys.platform,))


if __name__ == "__main__":
    main()
