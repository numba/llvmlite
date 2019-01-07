export ARCH="i686"
export PRECMD="linux32"
export MINICONDA_FILE="Miniconda3-3.19.0-Linux-x86.sh"
cd $(dirname $0)
./docker_run.sh $1 $2
