#!/usr/bin/env python
"""
Build script for the shared library providing the C ABI bridge to LLVM.
"""

from __future__ import print_function

from ctypes.util import find_library
import re
import multiprocessing
import os
import subprocess
import shutil
import sys
import tempfile


here_dir = os.path.abspath(os.path.dirname(__file__))
build_dir = os.path.join(here_dir, 'build')
target_dir = os.path.join(os.path.dirname(here_dir), 'llvmlite', 'binding')

is_64bit = sys.maxsize >= 2**32


def try_cmake(cmake_dir, build_dir, generator, arch=None, toolkit=None):
    old_dir = os.getcwd()
    args = ['cmake', '-G', generator]
    if arch is not None:
        args += ['-A', arch]
    if toolkit is not None:
        args += ['-T', toolkit]
    args.append(cmake_dir)
    try:
        os.chdir(build_dir)
        print('Running:', ' '.join(args))
        subprocess.check_call(args)
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


def find_windows_generator():
    """
    Find a suitable cmake "generator" under Windows.
    """
    # XXX this assumes we will find a generator that's the same, or
    # compatible with, the one which was used to compile LLVM... cmake
    # seems a bit lacking here.
    cmake_dir = os.path.join(here_dir, 'dummy')
    # LLVM 9.0 and later needs VS 2017 minimum.
    generators = []
    env_generator = os.environ.get("CMAKE_GENERATOR", None)
    if env_generator is not None:
        env_arch = os.environ.get("CMAKE_GENERATOR_ARCH", None)
        env_toolkit = os.environ.get("CMAKE_GENERATOR_TOOLKIT", None)
        generators.append(
            (env_generator, env_arch, env_toolkit)
        )

    generators.extend([
        # use VS2017 toolkit on VS2019 to match how llvmdev is built
        ('Visual Studio 16 2019', ('x64' if is_64bit else 'Win32'), 'v141'),
        # This is the generator configuration for VS2017
        ('Visual Studio 15 2017' + (' Win64' if is_64bit else ''), None, None)
    ])
    for generator in generators:
        build_dir = tempfile.mkdtemp()
        print("Trying generator %r" % (generator,))
        try:
            try_cmake(cmake_dir, build_dir, *generator)
        except subprocess.CalledProcessError:
            continue
        else:
            # Success
            return generator
        finally:
            shutil.rmtree(build_dir)
    raise RuntimeError("No compatible cmake generator installed on this machine")


def main_windows():
    generator = find_windows_generator()
    config = 'Release'
    if not os.path.exists(build_dir):
        os.mkdir(build_dir)
    # Run configuration step
    try_cmake(here_dir, build_dir, *generator)
    subprocess.check_call(['cmake', '--build', build_dir, '--config', config])
    shutil.copy(os.path.join(build_dir, config, 'llvmlite.dll'), target_dir)


def main_posix_cmake(kind, library_ext):
    generator = 'Unix Makefiles'
    config = 'Release'
    if not os.path.exists(build_dir):
        os.mkdir(build_dir)
    try_cmake(here_dir, build_dir, generator)
    subprocess.check_call(['cmake', '--build', build_dir, '--config', config])
    shutil.copy(os.path.join(build_dir, 'libllvmlite' + library_ext), target_dir)

def main_posix(kind, library_ext):
    if os.environ.get("LLVMLITE_USE_CMAKE", "0") == "1":
        return main_posix_cmake(kind, library_ext)

    os.chdir(here_dir)
    # Check availability of llvm-config
    llvm_config = os.environ.get('LLVM_CONFIG', 'llvm-config')
    print("LLVM version... ", end='')
    sys.stdout.flush()
    try:
        out = subprocess.check_output([llvm_config, '--version'])
    except FileNotFoundError:
        msg = ("Could not find a `llvm-config` binary. There are a number of "
               "reasons this could occur, please see: "
               "https://llvmlite.readthedocs.io/en/latest/admin-guide/"
               "install.html#using-pip for help.")
        # Raise from None, this is to hide the file not found for llvm-config
        # as this tends to cause users to install an LLVM which may or may not
        # work. Redirect instead to some instructions about how to deal with
        # this issue.
        raise RuntimeError(msg) from None
    except (OSError, subprocess.CalledProcessError) as e:
        raise RuntimeError("%s failed executing, please point LLVM_CONFIG "
                           "to the path for llvm-config" % (llvm_config,))

    out = out.decode('latin1')
    print(out)

    # See if the user is overriding the version check, this is unsupported
    try:
        _ver_check_skip = os.environ.get("LLVMLITE_SKIP_LLVM_VERSION_CHECK", 0)
        skipcheck = int(_ver_check_skip)
    except ValueError as e:
        msg = ('If set, the environment variable '
               'LLVMLITE_SKIP_LLVM_VERSION_CHECK should be an integer, got '
               '"{}".')
        raise ValueError(msg.format(_ver_check_skip)) from e

    if skipcheck:
        # user wants to use an unsupported version, warn about doing this...
        msg = ("The LLVM version check for supported versions has been "
               "overridden.\nThis is unsupported behaviour, llvmlite may not "
               "work as intended.\nRequested LLVM version: {}".format(
                   out.strip()))
        warn = ' * '.join(("WARNING",) * 8)
        blk = '=' * 80
        warning = '{}\n{}\n{}'.format(blk, warn, blk)
        print(warning)
        print(msg)
        print(warning + '\n')
    else:

        if not out.startswith('11'):
            msg = ("Building llvmlite requires LLVM 11.x.x, got "
                   "{!r}. Be sure to set LLVM_CONFIG to the right executable "
                   "path.\nRead the documentation at "
                   "http://llvmlite.pydata.org/ for more information about "
                   "building llvmlite.\n".format(out.strip()))
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
    svml_indicator = os.path.join(include_dir, 'llvm', 'IR', 'SVML.inc')
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
    try:
        default_makeopts = "-j%d" % (multiprocessing.cpu_count(),)
    except NotImplementedError:
        default_makeopts = ""
    makeopts = os.environ.get('LLVMLITE_MAKEOPTS', default_makeopts).split()
    subprocess.check_call(['make', '-f', makefile] + makeopts)
    shutil.copy('libllvmlite' + library_ext, target_dir)


def main():
    if sys.platform == 'win32':
        main_windows()
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
