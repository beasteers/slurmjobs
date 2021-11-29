Sample Files 
====================

This is a quick sample of the generated files.



Singularity
-------------

We have:

 - ``jobs/{name}/{job_id}.sbatch``: The sbatch file for each job.
 - ``jobs/{name}/run.sh``: A script that submits all jobs at once.

.. exec-code::

   import slurmjobs

   jobs = slurmjobs.Singularity(
      'python train.py', name='sing', backup=False,
      email='me@nyu.edu', n_gpus=2)

   run_script, job_paths = jobs.generate([
      ('model', ['AVE', 'AVOL']),
      ('audio_channels', [1, 2]),
   ], epochs=500)

   slurmjobs.util.summary(run_script, job_paths)


.. show-files::
   :filename: jobs/sing/*.sbatch

.. show-files::
   :filename: jobs/sing/run.sh




Slurm
--------

We have:

 - ``jobs/{name}/{job_id}.sbatch``: The sbatch file for each job.
 - ``jobs/{name}/run.sh``: A script that submits all jobs at once.

.. exec-code::

   import slurmjobs

   jobs = slurmjobs.Slurm(
      'python train.py', name='slurm', backup=False,
      email='me@nyu.edu', n_gpus=2)

   run_script, job_paths = jobs.generate([
      ('model', ['AVE', 'AVOL']),
      ('audio_channels', [1, 2]),
   ], epochs=500)

   slurmjobs.util.summary(run_script, job_paths)


.. show-files::
   :filename: jobs/slurm/*.sbatch

.. show-files::
   :filename: jobs/slurm/run.sh


Shell
--------

We have:

 - ``jobs/{name}/{job_id}.job.sh``: The shell file for each job.
 - ``jobs/{name}/run.sh``: A script that submits all jobs at once.

.. exec-code::

   import slurmjobs

   jobs = slurmjobs.Shell(
      'python train.py', name='shell', backup=False,
      email='me@nyu.edu', n_gpus=2)

   run_script, job_paths = jobs.generate([
      ('model', ['AVE', 'AVOL']),
      ('audio_channels', [1, 2]),
   ], epochs=500)

   slurmjobs.util.summary(run_script, job_paths)



.. show-files::
   :filename: jobs/shell/*.job.sh

.. show-files::
   :filename: jobs/shell/run.sh
