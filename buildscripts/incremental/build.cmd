
call activate %CONDA_ENV%

@rem LLVM derives the location of diaguids.lib from the build-time environment.
@rem Conda-forge packaging works around this by substituting the build-time
@rem location of Visual Studio with $ENV{VSINSTALLDIR}. In order to ensure that
@rem this environment variable is set appropriately, we activate the Visual
@rem Studio Developer Command Prompt prior to running setup.py
@rem
@rem This workaround is required whilst using LLVM from conda-forge; it may also
@rem be necessary to consider a workaround for our own llvmdev packages.
@rem
@rem For more info, see:
@rem
@rem - https://github.com/conda-forge/llvmdev-feedstock/issues/175
@rem - https://github.com/conda-forge/llvmdev-feedstock/pull/223
@rem - https://github.com/MicrosoftDocs/visualstudio-docs/issues/7774

python setup.py build
