# See all the notes in the `.sh` version of this file. We're doing
# basically the same thing, but we're going to reference into the
# conda environment using `LLVMConfig.cmake`, as the Windows build
# won't find things using `llvm-config`. The Windows version is
# slightly more path fragile, since we can't as easily stick
# `${HOME}` into things and have the interpolation work and the UNIX
# tools don't respect the `%USERPROFILE%` expansions. We're just
# going to reference absolute paths in  `config.toml`, which
# `cibuildwheel` uses as configuration. Should these paths change,
# there's a command at the end to dump any file paths that seem like
# matches, so you, dear reader, can pick them out of the logged
# wreckage of a failed build.
#
# It is also worth noting that cmake is a cauldron of lies about
# variable names. It's going its own detection method for packages
# and has really bad distinction in the documentation between
# internal variables, command line argument variables, and
# environment variables and to what degree those are actually
# distinct and whether those are meant to point to what Autotools
# users would called `--prefix` or the directory containing the file.
# So, we need to set `LLVM_DIR` as an environment variable to the
# location where the `LLVMConfig.cmake` file exists. Now, because of llvmlite's
# build process that changes directories and cibuildwheel's love of changing
# directories, we can only ever feed it absolute paths.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$PSDefaultParameterValues['*:ErrorAction']='Stop'
function ThrowOnNativeFailure {
    if (-not $?)
    {
        throw 'Native Failure'
    }
}

Invoke-WebRequest -Uri "https://repo.continuum.io/miniconda/Miniconda3-latest-Windows-x86_64.exe" -OutFile "miniconda.exe"

mkdir miniconda3
Start-Process miniconda.exe -Wait -ArgumentList @('/S',"/D=$(Get-Location)\miniconda3")
./miniconda3/condabin/conda.bat install numba::llvmdev=14

## Uncomment to see where the LLVMConfig.cmake file lives
# Get-ChildItem -Path miniconda3 -Filter LLVMConfig.cmake -Recurse -ErrorAction SilentlyContinue -Force
