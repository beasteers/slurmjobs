import glob
import setuptools

import os, imp
version = imp.load_source(
    'slurmjobs.__version__', 
    os.path.join(os.path.dirname(__file__), 'slurmjobs/__version__.py')).__version__


setuptools.setup(name='slurmjobs',
                 version=version,
                 description='Generate slurm jobs in batches.',
                 long_description=open('README.md').read().strip(),
                 long_description_content_type='text/markdown',
                 author='Bea Steers',
                 author_email='bea.steers@gmail.com',
                 # url='http://path-to-my-packagename',
                 package_data={'slurmjobs': ['templates/*.j2']},
                 scripts=glob.glob('scripts/**/*.sh'),
                 packages=setuptools.find_packages(),
                 install_requires=['pathtrees', 'Jinja2'],
                 license=open('README.md').readline().strip(),
                 extras_require={
                    'test': ['pytest', 'pytest-cov'],
                    'doc': ['sphinx']
                },
                 keywords='slurm sbatch job batch generation parameters ml machine learning python')
