@rem The cmd /C hack circumvents a regression where conda installs a conda.bat
@rem script in non-root environments.
set CONDA_INSTALL=cmd /C conda install -q -y
set PIP_INSTALL=pip install -q

@echo on

@rem Deactivate any environment
call deactivate
@rem Display root environment (for debugging)
conda list
@rem Clean up any left-over from a previous build
conda remove --all -q -y -n %CONDA_ENV%

@rem Create and populate environment
conda create -n %CONDA_ENV% -q -y python=%PYTHON% cmake
if %errorlevel% neq 0 exit /b %errorlevel%

call activate %CONDA_ENV%
if %errorlevel% neq 0 exit /b %errorlevel%

@rem Install llvmdev
%CONDA_INSTALL% -c numba llvmdev="10.0*"
if %errorlevel% neq 0 exit /b %errorlevel%
