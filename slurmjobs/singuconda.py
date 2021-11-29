import os
import subprocess
import slurmjobs

OVERLAY_DIR = "/scratch/work/public/overlay-fs-ext3/"
SIF_DIR = "/scratch/work/public/singularity"
 
def singuconda(overlay, sif, package=None, requirements=None, install=None, conda_env=None, python_version=None,
               sif_dir=SIF_DIR, overlay_dir=OVERLAY_DIR, overlay_src=None):
    '''Installing conda in a singularity overlay.
    
    Arguments:
        overlay (str): The path to the local overlay file.
        sif (str): The name of the sif file (either relative to ``sif_dir`` or an absolute path)

        package (str): a local python package: a repo directory containing a ``setup.py`` file where your project source lives.
            i.e. ``pip install -e ./your/package`` - you provide: ``./your/package``
        requirements (str): a pip requirements file: 
            i.e. ``pip install -r ./your/requirements.txt`` - you provide: ``./your/requirements.txt``
        install (str, list): any conda packages that you want to install: conda packages
            i.e. ``conda install numpy librosa`` - you provide: ``numpy librosa``

        conda_env (str): The name of a conda environment. If neither this, nor python version is provided, 
            the base environment will be used. If this is not defined and a python version is specified, 
            the conda environment will be ``f'py{python_version}'``
        python_version (str): The python version to use.

        sif_dir (str): Where the sif files are stored. This is ignored if an absolute path is provided for ``sif``.
            This just makes it more convenient to specify a sif file, under the assumption that you're using 
            NYU's provided sifs.
        overlay_dir (str): Where the zipped overlays are stored.
        overlay_src (str): 

    
    '''
    overlay_src = os.path.join(overlay_dir or '', overlay_src or f'{overlay}.gz')
    subprocess.run(f'''
OVERLAY="{overlay}"
OVERLAY_SRC="{overlay_src}"
''' + '''
# get overlay
if [ ! -f "${OVERLAY}" ]; then
    echo pulling overlay file...
    [ -f "${OVERLAY}.gz" ] || cp -rp "$OVERLAY_SRC" "${OVERLAY}.gz"
    echo unzipping overlay file...
    gunzip "${OVERLAY}.gz"
fi
    ''')

    header('setting up conda')

    # overlay = os.path.join(overlay_dir or '', overlay)
    sif = os.path.join(sif_dir or '', sif)

    if python_version and not conda_env:
        conda_env = f'py{python_version}'

    sing(overlay, sif, f"""
CONDA_ENV="{conda_env or ''}"
CONDA_PYTHON="{f'python={python_version}' if python_version else ''}"
""" + """
if [ ! -e /ext3/miniconda3 ]; then
    echo installing miniconda inside container...
    [[ ! -f Miniconda3-latest-Linux-x86_64.sh ]] && wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /ext3/miniconda3
fi

echo Updating conda
conda update -n base conda -y
[ ! -e "/ext3/miniconda3/$CONDA_ENV" ] && conda create -n $CONDA_ENV $CONDA_PYTHON  -y
conda install pip -y --upgrade

echo creating startup script
cat > /ext3/env << EOF2""" + r"""
#!/bin/bash
export PATH=/ext3/miniconda3/bin:\\\$PATH
source /ext3/miniconda3/etc/profile.d/conda.sh -y
conda activate $CONDA_ENV
echo "hello :) you're using:" "\\\$(which python)" "\\\$(python --version)"
EOF2

chmod +x /ext3/env
echo '/bin/bash --init-file /ext3/env' > /ext3/bash.env
chmod +x /ext3/bash.env
    """)


    header('installing packages in conda')

    sing(overlay, sif, f"""
REQUIREMENTS={requirements or ''}
INSTALLS={install or ''}
EDITABLE={package or ''}
""" + """
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
    """)

    cmd_alias = 'sing'
    cmd = sing_cmd(overlay, sif)
    with open(cmd_alias, 'w') as f:
        f.write(cmd)
    slurmjobs.util.make_executable(cmd_alias)

    header(f"to run a bash shell in the container:{cmd}\n  (alias: ``{cmd_alias}``)")


def sing(overlay, sif, code):
    subprocess.run(f"""
singularity exec --overlay {overlay} {sif} /bin/bash << EOF
[[ -f /ext3/env ]] && . /ext3/env
{code}
EOF
    """)

def sing_cmd(overlay, sif):
    return f"singularity exec --overlay {overlay} {sif} /bin/bash --init-file /ext3/env"


def header(*text):
    print()
    print('*****')
    print()
    print(*text)
    print()
    print('*****')
    print()
