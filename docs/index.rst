.. slurmjobs documentation master file, created by
   sphinx-quickstart on Wed Nov 24 17:43:34 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

slurmjobs 🐌
===============
Automating Slurm job generation.

Generate a set of `.sbatch` files over a grid of parameters. A run 
script is created which will submit all generated jobs as once.

Now with :func:`slurmjobs.Singularity` support!

You can also use `Shell` which excludes the slurm/module references so you can test & run 
on your local machine or test server.

Installation
---------------

.. code-block:: bash

   pip install slurmjobs==1.0.0a1

.. note::

   this is a pre-release until after paper-submission/holiday time when I can review it with my ✨friends✨ and they can critique it!

Usage
---------------

.. exec-code::

   import slurmjobs

   jobs = slurmjobs.Singularity(
      'python train.py', email='me@nyu.edu', n_gpus=2)

   # generate jobs across parameter grid
   run_script, job_paths = jobs.generate([
      # two different model types
      ('model', ['AVE', 'AVOL']),
      # try mono and stereo audio
      ('audio_channels', [1, 2]),
   ], epochs=500)

   # NOTE:
   #       extra keywords (e.g. ``epochs``) are also passed as arguments
   #       across all scripts and are not included in the job name.

   # ******************************
   # ** everything was generated ** - now let's see the outputted paths.

   slurmjobs.util.summary(run_script, job_paths)



.. toctree::
   :maxdepth: 2
   :titlesonly:
   :hidden:

   self


.. toctree::
   :maxdepth: 1
   :caption: Getting Started:

   tutorial
   sample

.. toctree::
   :maxdepth: 1
   :caption: API documentation

   jobs
   grid
   args
   receipt
   changes



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
