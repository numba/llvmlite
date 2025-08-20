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
import warnings


here_dir = os.path.abspath(os.path.dirname(__file__))
build_dir = os.path.join(here_dir, 'build')
target_dir = os.path.join(os.path.dirname(here_dir), 'llvmlite', 'binding')


is_64bit = sys.maxsize >= 2**32


def env_var_options_to_cmake_options():
    # This is not ideal, it exists to put env var options into CMake. Whilst it
    # is possible to pass options through setuptools/distutils etc, this is not
    # ideal either esp as the packaging system could do with an overhaul to meet
    # modern standards. Also, adding these as options to the CMake configuration
    # opposed to getting CMake to parse the env vars means that in the future it
    # is easier to extract the `ffi` library as a `libllvmlite` package such
    # that it can be built against multiple LLVM versions using a CMake
    # driven toolchain.
    cmake_options = []

    env_vars = {"LLVMLITE_PACKAGE_FORMAT": ("conda", "wheel"),
                "LLVMLITE_USE_RTTI": ("ON", "OFF", ""),
                "LLVMLITE_CXX_STATIC_LINK": bool,
                "LLVMLITE_SHARED": bool,
                "LLVMLITE_FLTO": bool,
                "LLVMLITE_SKIP_LLVM_VERSION_CHECK": bool,}

    for env_var in env_vars.keys():
        env_value = os.environ.get(env_var, None)
        if env_value is not None:
            expected_value = env_vars[env_var]
            if expected_value is bool:
                if env_value.lower() in ("true",  "on", "yes", "1", "y"):
                    cmake_options.append(f"-D{env_var}=ON")
                elif env_value.lower() in ("false",  "off", "no", "0", "n", ""):
                    cmake_options.append(f"-D{env_var}=OFF")
                else:
                    msg = ("Unexpected value found for build configuration "
                           f"environment variable '{env_var}={env_value}', "
                           "expected a boolean or unset.")
                    raise ValueError(msg)
            else:
                if env_value in expected_value:
                    cmake_options.append(f"-D{env_var}={env_value}")
                elif env_value == "":
                    # empty is fine
                    pass
                else:
                    msg = ("Unexpected value found for build configuration "
                           f"environment variable '{env_var}={env_value}', "
                           f"expected one of {expected_value} or unset.")
                    raise ValueError(msg)

    # Are there any `LLVMLITE_` prefixed env vars which are unused? (perhaps a
    # spelling mistake/typo)
    llvmlite_env_vars = set(k for k in os.environ.keys()
                            if k.startswith("LLVMLITE_"))
    unknown_env_vars = llvmlite_env_vars - set(env_vars.keys())
    if unknown_env_vars:
        msg = "Unknown LLVMLITE_ prefixed environment variables found:\n"
        msg += "\n".join([f"- {x}" for x in unknown_env_vars])
        msg += "\nIs this intended?"
        warnings.warn(msg)

    return cmake_options


def try_cmake(cmake_dir, build_dir, generator, arch=None, toolkit=None):
    old_dir = os.getcwd()
    args = ['cmake', '-G', generator]
    if arch is not None:
        args += ['-A', arch]
    if toolkit is not None:
        args += ['-T', toolkit]
    args.append(cmake_dir)
    cmake_options = env_var_options_to_cmake_options()
    args += cmake_options
    try:
        os.chdir(build_dir)
        print('Running:', ' '.join(args))
        subprocess.check_call(args)
    finally:
        os.chdir(old_dir)


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
        # use VS2022 first
        ('Visual Studio 17 2022', ('x64' if is_64bit else 'Win32'), 'v143'),
        # try VS2019 next
        ('Visual Studio 16 2019', ('x64' if is_64bit else 'Win32'), 'v142'),
        # # This is the generator configuration for VS2017
        # ('Visual Studio 15 2017' + (' Win64' if is_64bit else ''), None, None)
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
    raise RuntimeError("No compatible CMake generator could be found.")


def remove_msvc_whole_program_optimization():
    """Remove MSVC whole-program optimization flags.
    This workaround a segfault issue on windows.
    Note: conda-build is known to enable the `-GL` flag.
    """
    def drop_gl(flags):
        try:
            flags.remove('-GL')
        except ValueError:
            pass
        else:
            print(f"removed '-GL' flag in {flags}")
    cflags = os.environ.get('CFLAGS', '').split(' ')
    cxxflags = os.environ.get('CXXFLAGS', '').split(' ')
    drop_gl(cflags)
    drop_gl(cxxflags)
    os.environ['CFLAGS'] = ' '.join(cflags)
    os.environ['CXXFLAGS'] = ' '.join(cxxflags)


def main_windows():
    remove_msvc_whole_program_optimization()
    generator = find_windows_generator()
    config = 'Release'
    if not os.path.exists(build_dir):
        os.mkdir(build_dir)
    # Run configuration step
    try_cmake(here_dir, build_dir, *generator)
    subprocess.check_call(['cmake', '--build', build_dir, '--config', config])
    shutil.copy(os.path.join(build_dir, config, 'llvmlite.dll'), target_dir)


def main_posix(library_ext):
    generator = 'Unix Makefiles'
    config = 'Release'
    if not os.path.exists(build_dir):
        os.mkdir(build_dir)
    try_cmake(here_dir, build_dir, generator)
    cmd = ['cmake', '--build', build_dir, "--parallel", '--config', config]
    subprocess.check_call(cmd)
    shutil.copy(os.path.join(build_dir, 'libllvmlite' + library_ext),
                target_dir)


def main():
    ELF_systems = ('linux', 'gnu', 'freebsd', 'openbsd', 'netbsd')
    if sys.platform == 'win32':
        main_windows()
    elif sys.platform.startswith(ELF_systems):
        main_posix('.so')
    elif sys.platform == 'darwin':
        main_posix('.dylib')
    else:
        raise RuntimeError("unsupported platform: %r" % (sys.platform,))


if __name__ == "__main__":
    main()
