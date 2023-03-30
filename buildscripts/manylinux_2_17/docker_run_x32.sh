export ARCH="i686"
export PRECMD="linux32"
export MINICONDA_FILE="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86.sh"
cd $(dirname $0)
./docker_run.sh $1 $2
