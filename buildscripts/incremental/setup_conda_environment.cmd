@echo on

@rem Display root environment (for debugging)
call conda list

@rem Create and populate environment
call conda create -n %CONDA_ENV% -q -y python=%PYTHON% cmake
if %errorlevel% neq 0 exit /b %errorlevel%

call activate %CONDA_ENV%
if %errorlevel% neq 0 exit /b %errorlevel%

@rem Install llvmdev 20
call conda install -y -c defaults numba/label/dev::llvmdev=20 libxml2
if %errorlevel% neq 0 exit /b %errorlevel%
