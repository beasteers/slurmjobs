#!/bin/bash

# Setting up a Singularity Container with Conda and a python environment
# It will prompt you for the information when you run the command
#
# Source Tutorial: https://sites.google.com/a/nyu.edu/nyu-hpc/services/Training-and-Workshops/tutorials/singularity-on-greene

OVERLAY_DIR=""
SIF_DIR="/scratch/work/public/singularity"

DEFAULT_OVERLAY=${1:-"overlay-5GB-200K.ext3"}
DEFAULT_SIF=${2:-"cuda11.0-cudnn8-devel-ubuntu18.04.sif"}

header() {
    echo 
    echo '*****'
    echo 
    echo $@
    echo
    echo '*****'
    echo 
}

cat << EOF
      ___                       ___           ___           ___                         ___           ___                                         
     /  /\        ___          /__/\         /  /\         /__/\                       /  /\         /  /\        ___           ___         ___   
    /  /:/_      /  /\         \  \:\       /  /:/_        \  \:\                     /  /::\       /  /::\      /  /\         /  /\       /__/|  
   /  /:/ /\    /  /:/          \  \:\     /  /:/ /\        \  \:\    ___     ___    /  /:/\:\     /  /:/\:\    /  /:/        /  /:/      |  |:|  
  /  /:/ /::\  /__/::\      _____\__\:\   /  /:/_/::\   ___  \  \:\  /__/\   /  /\  /  /:/~/::\   /  /:/~/:/   /__/::\       /  /:/       |  |:|  
 /__/:/ /:/\:\ \__\/\:\__  /__/::::::::\ /__/:/__\/\:\ /__/\  \__\:\ \  \:\ /  /:/ /__/:/ /:/\:\ /__/:/ /:/___ \__\/\:\__   /  /::\     __|__|:|  
 \  \:\/:/~/:/    \  \:\/\ \  \:\~~\~~\/ \  \:\ /~~/:/ \  \:\ /  /:/  \  \:\  /:/  \  \:\/:/__\/ \  \:\/:::::/    \  \:\/\ /__/:/\:\   /__/::::\\  
  \  \::/ /:/      \__\::/  \  \:\  ~~~   \  \:\  /:/   \  \:\  /:/    \  \:\/:/    \  \::/       \  \::/~~~~      \__\::/ \__\/  \:\     ~\~~\:\\ 
   \__\/ /:/       /__/:/    \  \:\        \  \:\/:/     \  \:\/:/      \  \::/      \  \:\        \  \:\          /__/:/       \  \:\      \  \:\\
     /__/:/        \__\/      \  \:\        \  \::/       \  \::/        \__\/        \  \:\        \  \:\         \__\/         \__\/       \__\/
     \__\/                     \__\/         \__\/         \__\/                       \__\/         \__\/                                        
	&
    ___       ___       ___       ___       ___
   /\  \     /\  \     /\__\     /\  \     /\  \\
  /::\  \   /::\  \   /:| _|_   /::\  \   /::\  \\
 /:/\:\__\ /:/\:\__\ /::|/\__\ /:/\:\__\ /::\:\__\\
 \:\ \/__/ \:\/:/  / \/|::/  / \:\/:/  / \/\::/  /
  \:\__\    \::/  /    |:/  /   \::/  /    /:/  /
   \/__/     \/__/     \/__/     \/__/     \/__/
EOF


header "Let's build a singularity anaconda container asdsafjaskd !!!"

cat << EOF
The information that you can configure (everything has defaults so you can smash enter if you really just don't care):
 1. Singularity options:
    - overlay file: This is where the data gets stored. We will copy this 
        to the current directory and install packages into this.
    - sif file: This is your base image that gives you default libraries (like cuda)
 2. Conda options (all below are optional)
    - a pip requirements file: 
        i.e. ``pip install -r ./your/requirements.txt`` - you provide: ``./your/requirements.txt``
    - a local python package: a repo directory containing a ``setup.py`` file where your project source lives.
         i.e. ``pip install -e ./your/package`` - you provide: ``./your/package``
    - any conda packages that you want to install: conda packages
        i.e. ``conda install numpy librosa`` - you provide: ``numpy librosa``
What's going to happen:
 1. First we ask you for the information above
 2. Then we copy the overlay file to your current directory
 3. We then enter the singularity container and install miniconda
 4. Then we install all of the pip/conda stuff you requested
 5. Then you're all set! :) cause some chaos, request some gpus, idk
EOF


header first we need some information:

echo 
echo '--'
echo Singularity Options:

echo Available Overlays:
ls /scratch/work/public/overlay-fs-ext3/
echo 
read -e -p "What overlay file should we use? (don't include path/ and .gz) [$DEFAULT_OVERLAY] " OVERLAY
OVERLAY=${OVERLAY:-$DEFAULT_OVERLAY}
#if [ ! -f "$OVERLAY"] && [ -f "$OVERLAY_DIR/$OVERLAY" ]; then OVERLAY="$OVERLAY_DIR/$OVERLAY"; fi

echo
echo Available sifs:
ls /scratch/work/public/singularity/*.sif
read -e -p "What sif file should we use? (full path) [$DEFAULT_SIF] " SIF
SIF=${SIF:-$DEFAULT_SIF}
if [ ! -f "$SIF" ] && [ -f "$SIF_DIR/$SIF" ]; then SIF="$SIF_DIR/$SIF"; fi

echo
echo '--'
echo Conda Options:

echo
read -e -p "Do you want to use a specific Python version? [miniconda python3 default] "$'\n'"    python=" PYTHON_VERSION

echo
read -e -p "Is there a pip requirements file you want to install? (provide the path) [none] "$'\n'"    pip install -r " REQUIREMENTS
if [ ! -f "$REQUIREMENTS"] && [ -d "$REQUIREMENTS" ] && [ -f "${REQUIREMENTS}/requirements.txt" ]; then
    REQUIREMENTS="${REQUIREMENTS}/requirements.txt"
fi

echo
read -e -p "Do you have a custom python package that you want to be editable? (provide the path) [none] "$'\n'"    pip install -e " EDITABLE

echo
read -p "Are there any conda packages you want to install? "$'\n'"    conda install " PACKAGES






header locating overlay: $OVERLAY


# get overlay
if [ ! -f "${OVERLAY}" ]; then
    echo pulling overlay file...
    [ -f "${OVERLAY}.gz" ] || cp -rp "$OVERLAY_DIR"/"${OVERLAY}.gz" "${OVERLAY}.gz"
    echo unzipping overlay file...
    gunzip "${OVERLAY}.gz"
fi

header setting up conda

CONDA_ENV='singularity'

singularity exec --overlay $OVERLAY $SIF /bin/bash << EOF
if [ ! -e /ext3/miniconda3 ]; then
    echo installing miniconda inside container...
    [[ ! -f Miniconda3-latest-Linux-x86_64.sh ]] && wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /ext3/miniconda3
fi
echo updating conda versions
export PATH=/ext3/miniconda3/bin:\$PATH
conda update -n base conda -y
#if [ ! -z PYTHON_VERSION ]; then CONDA_PYTHON="python=$PYTHON_VERSION"; fi
[ ! -z $CONDA_ENV ] && [ ! -e "/ext3/miniconda3/$CONDA_ENV" ] && conda create -n $CONDA_ENV python=$PYTHON_VERSION -y
conda install pip -y
echo creating startup script
cat > /ext3/env << EOF2
#!/bin/bash
export PATH=/ext3/miniconda3/bin:\\\$PATH
source /ext3/miniconda3/etc/profile.d/conda.sh -y
conda activate $CONDA_ENV
echo "hello :) you're using:" "\\\$(which python)" "\\\$(python --version)"
#[ -e ~/.bashrc ] && . ~/.bashrc
EOF2
chmod +x /ext3/env
echo '/bin/bash --init-file /ext3/env' > /ext3/bash.env
chmod +x /ext3/bash.env
EOF

header setting up conda

singularity exec --overlay $OVERLAY $SIF /bin/bash << EOF
. /ext3/env
echo Doing installs...
echo requirements file: "$REQUIREMENTS"
if [ ! -z "$REQUIREMENTS" ]; then
    echo 'installing pip requirements file:' "$REQUIREMENTS"
    pip install -r $REQUIREMENTS
fi
echo packages to install: "$INSTALLS"
if [ ! -z "$INSTALLS" ]; then
    echo 'installing custom conda packages:' "$INSTALLS"
    conda install $INSTALLS
fi
echo project package: "$EDITABLE"
if [ ! -z "$EDITABLE" ]; then
    echo 'installing python package:' "$EDITABLE"
    pip install -e $EDITABLE
fi
conda clean --all --yes
EOF

export SINGULARITY_CMD="singularity exec --overlay $OVERLAY $SIF /bin/bash --init-file /ext3/env"

echo $SINGULARITY_CMD > ./sing
chmod +x ./sing

header "to run a bash shell in the container:" "``$SINGULARITY_CMD``" "\n  (alias: ``./sing``)"