export ARCH="ppc64le"
export MINICONDA_FILE="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-ppc64le.sh"
cd $(dirname $0)
./docker_run.sh $1 $2
