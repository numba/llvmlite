#!/usr/bin/env python
"""
Build script for the shared library providing the C ABI bridge to LLVM.
"""

from __future__ import print_function

from ctypes.util import find_library
import glob
import os
import subprocess
import shutil
import sys
import tempfile

here_dir = os.path.abspath(os.path.dirname(__file__))
build_dir = os.path.join(here_dir, 'build')
target_dir = os.path.join(os.path.dirname(here_dir), 'llvmlite', 'binding')

is_64bit = sys.maxsize >= 2 ** 32


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
    # Copy CRT libraries as well, so as to package them.
    if os.environ.get('PROCESSOR_ARCHITEW6432'):
        # Hard-code WoW64 path if we're a 32-bit Python in a 64-bit system,
        # otherwise the wrong DLL file will be found by find_library().
        search_path = r'c:\windows\syswow64'
    else:
        search_path = r'c:\windows\system32'
    for lib in ['msvcr120.dll', 'msvcp120.dll']:
        lib_path = os.path.join(search_path, lib)
        if not os.path.exists(lib_path):
            lib_path = find_library(lib)
            if lib_path is None:
                raise RuntimeError("%r not found" % (lib,))
        shutil.copy(lib_path, target_dir)


# POSIX platform code starts here

def get_compiler_args(kind):
    if kind in ('freebsd', 'osx'):
        compiler_args = ['clang++', '-std=c++11', '-stdlib=libc++']
    else:
        compiler_args = ['g++']
    compiler_args[0] = os.environ.get('CXX', compiler_args[0])
    return compiler_args


def try_static_compile(kind, build_dir, test_source_path):
    old_dir = os.getcwd()
    test_destfile = os.path.splitext(test_source_path)[0]
    try:
        os.chdir(build_dir)
        cmd_args = get_compiler_args(kind)
        cmd_args.extend(['-static-libstdc++', '-o', test_destfile, test_source_path])
        subprocess.check_call(cmd_args)
    finally:
        os.chdir(old_dir)


def can_use_static_libcpp(kind):
    """
    Return True if we can compile a simple C++ program with ``-static-libstdc++``.
    """
    build_dir = tempfile.mkdtemp()
    test_fd, test_path = tempfile.mkstemp(suffix='.cpp', dir=build_dir, text=True)
    try:
        os.write(test_fd, '#include <algorithm>\nint main() { return 0; }\n')
        os.close(test_fd)
        try_static_compile(kind, build_dir, test_path)
    except subprocess.CalledProcessError:
        pass
    else:
        return True
    finally:
        shutil.rmtree(build_dir)
    return False


def run_llvm_config(*config_args):
    """
    Run ``llvm-config`` with :attr:`config_args` and return the resulting output.
    """
    llvm_config = os.environ.get('LLVM_CONFIG', 'llvm-config')
    proc_args = [llvm_config]
    proc_args.extend(config_args)
    proc = subprocess.Popen(proc_args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    try:
        proc_out, _ = proc.communicate()
    except (OSError, subprocess.CalledProcessError):
        raise RuntimeError("%s failed executing, please point LLVM_CONFIG "
                           "to the path for llvm-config" % (llvm_config,))
    else:
        return proc_out.strip()


def get_posix_compiler_info(kind):
    cmd_dict = {'env': dict(**os.environ)}
    if kind == 'osx':
        # TODO: Why is this specifically 10.7? Does it break on <= 10.6?
        cmd_dict['env']['MACOSX_DEPLOYMENT_TARGET'] = '10.7'
    cmd_dict['cxx'] = get_compiler_args(kind)
    if kind == 'osx':
        cmd_dict['shared'] = ['-dynamiclib']
    else:
        cmd_dict['shared'] = ['-shared']
        if can_use_static_libcpp(kind):
            cmd_dict['shared'].insert(0, '-static-libstdc++')
    cmd_dict['cxxflags'] = run_llvm_config('--cxxflags').strip().split()
    if kind == 'linux':
        cmd_dict['cxxflags'].insert(0, '-flto')
        cmd_dict['cxxflags'].extend(['-fno-rtti', '-g'])
    # Source files are the same on all platforms
    cmd_dict['src'] = glob.glob('*.cpp')
    if kind == 'osx':
        cmd_dict['output'] = 'libllvmlite.dylib'
    else:
        cmd_dict['output'] = 'libllvmlite.so'
    cmd_dict['ldflags'] = run_llvm_config('--ldflags').strip().split()
    if kind == 'linux':
        cmd_dict['ldflags'].insert(0, '-flto')
        cmd_dict['ldflags'].append('-Wl,--exclude-libs=ALL')
        cmd_dict['libs'] = run_llvm_config('--system-libs', '--libs', 'all').strip().split()
        # TODO: Do we want to link in -lstdc++ if we can't use the static library?
    if '-static-libstdc++' not in cmd_dict['shared']:
        cmd_dict['libs'].append('-lstdc++')
    return cmd_dict


def main_posix(kind):
    os.chdir(here_dir)

    # Check availability of llvm-config
    llvm_config = os.environ.get('LLVM_CONFIG', 'llvm-config')
    llvm_version = run_llvm_config('--version')
    print("LLVM version... {0}".format(llvm_version))

    # Build list of compiler args in a platform-generic way.
    # Ordering: <cxx> <shared> <cxxflags> <src> -o <output> <ldflags> <libs>
    compiler_info = get_posix_compiler_info(kind)
    cmd_args = compiler_info['cxx'][:]
    cmd_args.extend(compiler_info['shared'])
    cmd_args.extend(compiler_info['cxxflags'])
    cmd_args.extend(compiler_info['src'])
    cmd_args.extend(['-o', compiler_info['output']])
    cmd_args.extend(compiler_info['ldflags'])
    cmd_args.extend(compiler_info['libs'])

    subprocess.check_call(cmd_args, env=compiler_info['env'])
    shutil.copy(compiler_info['output'], target_dir)


def main():
    if sys.platform == 'win32':
        main_win32()
    elif sys.platform.startswith('linux'):
        main_posix('linux')
    elif sys.platform.startswith('freebsd'):
        main_posix('freebsd')
    elif sys.platform == 'darwin':
        main_posix('osx')
    else:
        raise RuntimeError("unsupported platform: %r" % (sys.platform,))


if __name__ == "__main__":
    main()
