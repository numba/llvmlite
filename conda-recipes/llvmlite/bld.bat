
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
@rem for older VS:
@rem set CMAKE_GENERATOR=Visual Studio 15 2017
@rem do not set CMAKE_GENERATOR_TOOLKIT
set CMAKE_GENERATOR=Visual Studio 16 2019
set CMAKE_GENERATOR_TOOLKIT=v141

@rem Ensure there are no build leftovers (CMake can complain)
if exist ffi\build rmdir /S /Q ffi\build

%PYTHON% -S setup.py install
if errorlevel 1 exit 1

%PYTHON% runtests.py
if errorlevel 1 exit 1
