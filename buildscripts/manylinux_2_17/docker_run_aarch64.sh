export ARCH="aarch64"
export MINICONDA_FILE="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh"
cd $(dirname $0)
./docker_run.sh $1 $2
