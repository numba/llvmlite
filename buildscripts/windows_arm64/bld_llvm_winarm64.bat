@echo off
setlocal enabledelayedexpansion

set "LLVM_VERSION=20.1.8"
set "WORKSPACE=%CD%"
set "LLVM_SRC_DIR=%WORKSPACE%\llvm-project-%LLVM_VERSION%"
set "BUILD_DIR=%WORKSPACE%\build-arm64"
set "INSTALL_PREFIX=%WORKSPACE%\llvm-arm64-install"

REM Set environmental variable for VCPKG
set "VCPKG_DIR=C:\vcpkg"

REM Setup VS2022 ARM64 environment
call "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvarsall.bat" arm64

REM Install dependencies using vcpkg
"%VCPKG_DIR%\vcpkg.exe" install zlib:arm64-windows-static zstd:arm64-windows-static libxml2:arm64-windows-static

REM Download and extract LLVM source
if not exist "%LLVM_SRC_DIR%\llvm" (
    if not exist "llvm-project-%LLVM_VERSION%.src.tar.xz" (
        curl -L -o "llvm-project-%LLVM_VERSION%.src.tar.xz" "https://github.com/llvm/llvm-project/releases/download/llvmorg-%LLVM_VERSION%/llvm-project-%LLVM_VERSION%.src.tar.xz"
    )
    tar -xf "llvm-project-%LLVM_VERSION%.src.tar.xz"
    if exist "llvm-project-%LLVM_VERSION%.src" move "llvm-project-%LLVM_VERSION%.src" "llvm-project-%LLVM_VERSION%"
)

REM Configure
if exist "%BUILD_DIR%" rmdir /S /Q "%BUILD_DIR%"
mkdir "%BUILD_DIR%"
cd /d "%BUILD_DIR%"

cmake -G "Ninja" ^
    -DCMAKE_BUILD_TYPE=Release ^
    -DCMAKE_INSTALL_PREFIX=%INSTALL_PREFIX% ^
    -DCMAKE_TOOLCHAIN_FILE=%VCPKG_DIR%\scripts\buildsystems\vcpkg.cmake ^
    -DVCPKG_TARGET_TRIPLET=arm64-windows-static ^
    -DLLVM_USE_INTEL_JITEVENTS=OFF ^
    -DLLVM_ENABLE_LIBXML2=FORCE_ON ^
    -DLLVM_ENABLE_RTTI=OFF ^
    -DLLVM_ENABLE_ZLIB=FORCE_ON ^
    -DLLVM_ENABLE_ZSTD=FORCE_ON ^
    -DLLVM_INCLUDE_BENCHMARKS=OFF ^
    -DLLVM_INCLUDE_DOCS=OFF ^
    -DLLVM_INCLUDE_EXAMPLES=OFF ^
    -DLLVM_INCLUDE_TESTS=ON ^
    -DLLVM_INCLUDE_UTILS=ON ^
    -DLLVM_INSTALL_UTILS=ON ^
    -DLLVM_UTILS_INSTALL_DIR=libexec/llvm ^
    -DLLVM_BUILD_LLVM_C_DYLIB=no ^
    -DLLVM_EXPERIMENTAL_TARGETS_TO_BUILD=WebAssembly ^
    -DCMAKE_POLICY_DEFAULT_CMP0111=NEW ^
    -DLLVM_ENABLE_PROJECTS=lld ^
    -DLLVM_ENABLE_ASSERTIONS=ON ^
    -DLLVM_ENABLE_DIA_SDK=OFF ^
    -DBUILD_SHARED_LIBS=OFF ^
    "%LLVM_SRC_DIR%\llvm"

if !ERRORLEVEL! neq 0 exit /B 1

REM Build
cmake --build . --config Release
if !ERRORLEVEL! neq 0 exit /B 1

REM Install
cmake --build . --target install --config Release
if !ERRORLEVEL! neq 0 exit /B 1

cd /d "%WORKSPACE%"
exit /B 0
