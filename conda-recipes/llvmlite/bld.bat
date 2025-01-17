@rem Let CMake know about the LLVM install path, for find_package()
set CMAKE_PREFIX_PATH=%LIBRARY_PREFIX%

@rem VS2019 uses a different naming convention for platforms than older version
if "%ARCH%"=="32" (
    @rem VS2017:
    @rem set CMAKE_GENERATOR_ARCH=
    set CMAKE_GENERATOR_ARCH=Win32
) else (
    @rem VS2017
    @rem set CMAKE_GENERATOR_ARCH=Win64
    set CMAKE_GENERATOR_ARCH=x64
)
set CMAKE_GENERATOR=Visual Studio 16 2019
set CMAKE_GENERATOR_TOOLKIT=v142

@rem Ensure there are no build leftovers (CMake can complain)
if exist ffi\build rmdir /S /Q ffi\build

set "VS_VERSION=2019"
set "VS_PLATFORM=x64"
set "LLVM_ENABLE_DIA_SDK=OFF"
%PYTHON% setup.py clean
%PYTHON% setup.py install
if errorlevel 1 exit 1
