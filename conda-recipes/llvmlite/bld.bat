@rem This is Numba channel specific: declare this as a conda package
set LLVMLITE_PACKAGE_FORMAT=conda

@rem Let CMake know about the LLVM install path, for find_package()
set CMAKE_PREFIX_PATH=%LIBRARY_PREFIX%

@rem VS2022 uses a different naming convention for platforms than older version
if "%ARCH%"=="32" (
    @rem VS2022:
    @rem set CMAKE_GENERATOR_ARCH=
    set CMAKE_GENERATOR_ARCH=Win32
) else (
    @rem VS2022
    @rem set CMAKE_GENERATOR_ARCH=Win64
    set CMAKE_GENERATOR_ARCH=x64
)
set CMAKE_GENERATOR=Visual Studio 17 2022
set CMAKE_GENERATOR_TOOLKIT=v143

@rem Ensure there are no build leftovers (CMake can complain)
if exist ffi\build rmdir /S /Q ffi\build

%PYTHON% -m pip install --no-index --no-deps --no-build-isolation -vv .
if errorlevel 1 exit 1
