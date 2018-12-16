setlocal enabledelayedexpansion

set MSC_VER=12
set VC_PATH=x86
if "%ARCH%"=="64" (
   set VC_PATH=x64
)

FOR /F "usebackq tokens=3*" %%A IN (`REG QUERY "HKEY_LOCAL_MACHINE\Software\Microsoft\DevDiv\VC\Servicing\%MSC_VER%.0\RuntimeMinimum" /v UpdateVersion`) DO (
    set VER=%%A
    )


if not "%VER%" == "%PKG_VERSION%" (
   echo "Version detected from registry: %VER%"
   echo "does not match version of package being built (%PKG_VERSION%)"
   echo "Do you have current updates for VS 2013 installed?"
   exit 1
)

robocopy "C:\Program Files (x86)\Microsoft Visual Studio %MSC_VER%.0\VC\redist\%VC_PATH%\Microsoft.VC%MSC_VER%0.CRT" "%LIBRARY_BIN%" *.dll /E
robocopy "C:\Program Files (x86)\Microsoft Visual Studio %MSC_VER%.0\VC\redist\%VC_PATH%\Microsoft.VC%MSC_VER%0.CRT" "%PREFIX%" *.dll /E
robocopy "C:\Program Files (x86)\Microsoft Visual Studio %MSC_VER%.0\VC\redist\%VC_PATH%\Microsoft.VC%MSC_VER%0.OpenMP" "%LIBRARY_BIN%" *.dll /E
robocopy "C:\Program Files (x86)\Microsoft Visual Studio %MSC_VER%.0\VC\redist\%VC_PATH%\Microsoft.VC%MSC_VER%0.OpenMP" "%PREFIX%" *.dll /E
if %ERRORLEVEL% LSS 8 exit 0
