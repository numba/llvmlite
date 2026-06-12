@rem This is Numba channel specific: declare this as a conda package
set LLVMLITE_PACKAGE_FORMAT=conda

@rem Let CMake know about the LLVM install path, for find_package()
set CMAKE_PREFIX_PATH=%LIBRARY_PREFIX%

@rem VS2022 uses a different naming convention for platforms than older version
if "%ARCH%"=="32" (
    @rem VS2022:
    @rem set CMAKE_GENERATOR_ARCH=
    set CMAKE_GENERATOR_ARCH=Win32
) else if "%ARCH%"=="arm64" (
    set CMAKE_GENERATOR_ARCH=ARM64
) else (
    @rem VS2022
    @rem set CMAKE_GENERATOR_ARCH=Win64
    set CMAKE_GENERATOR_ARCH=x64
)
@rem v143 toolset for ABI parity with llvmdev (built with MSVC v14.44);
@rem VS2026 ships it as a compatibility component.
@rem ffi/build.py falls back to VS2022/VS2019 if this generator is absent.
set CMAKE_GENERATOR=Visual Studio 18 2026
set CMAKE_GENERATOR_TOOLKIT=v143

@rem Ensure there are no build leftovers (CMake can complain)
if exist ffi\build rmdir /S /Q ffi\build

%PYTHON% -m pip install --no-index --no-deps --no-build-isolation -vv .
if errorlevel 1 exit 1
