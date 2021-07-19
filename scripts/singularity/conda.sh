#!/bin/bash

# Setting up a Singularity Container with Conda and a python environment
# It will prompt you for the information when you run the command
#
# Source Tutorial: https://sites.google.com/a/nyu.edu/nyu-hpc/services/Training-and-Workshops/tutorials/singularity-on-greene

DEFAULT_OVERLAY=${1:-"overlay-5GB-200K.ext3"}
DEFAULT_SIF=${2:-"/scratch/work/public/singularity/cuda11.0-cudnn8-devel-ubuntu18.04.sif"}

header() {
    echo '*****'
    echo 
    echo $@
    echo
    echo '*****'
}




header first we need some information:

read -e -p "What overlay file should we use? [$DEFAULT_OVERLAY] " OVERLAY
OVERLAY=${OVERLAY:-$DEFAULT_OVERLAY}

read -e -p "What sif file should we use? [$DEFAULT_SIF] " SIF
SIF=${SIF:-$DEFAULT_SIF}

read -e -p "Is there a pip requirements file you want to install? (provide the path) [none] " REQUIREMENTS
if [ ! -f "$REQUIREMENTS"] && [ -d "$REQUIREMENTS" ] && [ -f "${REQUIREMENTS}/requirements.txt" ]; then
    REQUIREMENTS="${REQUIREMENTS}/requirements.txt"
fi

read -e -p "Do you have a custom python package that you want to be editable? (provide the path) [none] " EDITABLE

read -p "Are there any conda packages you want to install? i.e. conda install " PACKAGES






header locating overlay: $OVERLAY


# get overlay
if [ ! -f "${OVERLAY}" ]; then
    echo pulling overlay file...
    [ -f "${OVERLAY}.gz" ] || cp -rp /scratch/work/public/overlay-fs-ext3/"${OVERLAY}.gz" "${OVERLAY}.gz"
    echo unzipping overlay file...
    gunzip "${OVERLAY}.gz"
fi

header setting up conda

singularity exec --overlay $OVERLAY $SIF /bin/bash << EOF
if [ ! -e /ext3/miniconda3 ]; then
    echo installing miniconda inside container...
    [[ ! -f Miniconda3-latest-Linux-x86_64.sh ]] && wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /ext3/miniconda3
fi
echo updating conda versions
export PATH=/ext3/miniconda3/bin:\$PATH
conda update -n base conda -y
conda install pip -y
echo creating startup script
cat > /ext3/env << EOF2
#!/bin/bash
source /ext3/miniconda3/etc/profile.d/conda.sh -y
export PATH=/ext3/miniconda3/bin:\\\$PATH
conda activate base
echo "hello :) you're using:" "$(which python)" "$(python --version)"
EOF2
chmod +x /ext3/env
echo '/bin/bash --init-file /ext3/env' > /ext3/bash.env
chmod +x /ext3/bash.env
EOF

header setting up conda

singularity exec --overlay $OVERLAY $SIF /bin/bash << EOF
. /ext3/env
if [ -f "$REQUIREMENTS" ]; then
    echo 'installing pip requirements file:' "$REQUIREMENTS"
    pip install -r $REQUIREMENTS
fi
if [ -f "$INSTALLS" ]; then
    echo 'installing custom conda packages:' "$INSTALLS"
    conda install $INSTALLS
fi
if [ -f "$EDITABLE" ]; then
    echo 'installing python package:' "$EDITABLE"
    pip install -e $EDITABLE
fi
conda clean --all --yes
EOF

header "to run a bash shell in the container:" "singularity exec --overlay $OVERLAY $SIF /bin/bash --init-file /ext3/env"