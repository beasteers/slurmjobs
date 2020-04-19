import setuptools

setuptools.setup(name='slurmjobs',
                 version='0.0.3',
                 description='Generate slurm jobs in batches.',
                 long_description=open('README.md').read().strip(),
                 long_description_content_type='text/markdown',
                 author='Bea Steers',
                 author_email='bea.steers@gmail.com',
                 # url='http://path-to-my-packagename',
                 package_data={'slurmjobs': ['templates/*.j2']},
                 packages=setuptools.find_packages(),
                 install_requires=['pathtree', 'Jinja2'],
                 license='MIT License',
                 keywords='slurm sbatch job batch generation parameters ml machine learning python')
