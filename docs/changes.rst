
Changes
=============

Unreleased
-------------

 - Rewrote like 70% of the code, including: jinja templates, jobs base class and subclasses
 - added a :func:`slurmjobs.Singularity` class and template
 - added parameter grid classes!! Lets you do grid arithmetic :)
 - Renamed:

    - ``slurmjobs.Batch`` => :func:`slurmjobs.Jobs`
    - ``slurmjobs.SlurmBatch`` => :func:`slurmjobs.Slurm`
    - ``slurmjobs.Jobs.default_options`` => ``slurmjobs.Jobs.options``
    - ``slurmjobs.Jobs.JOB_ID_KEY`` => ``slurmjobs.Jobs.job_id_arg``

 - Changed signatures:

    - removed parameters from :func:`slurmjobs.Jobs.__init__`: ``multicmd, cmd_wrapper, init_script, run_init_script, post_script, paths``
    - added ``Receipt(receipt_id='a-str-used-instead-of-hash_args()')``

 - removed utilities:

    - ``get_job_name``, ``make_job_name_tpl``, ``format_value_for_name``, ``_encode_special``, ``_decode_special``, ``_obliterate_special``:
      replaced by :func:`slurmjobs.Jobs.format_id_item` and :func:`slurmjobs.Jobs.format_job_id`
    - ``expand_grid``, ``expand_paired_params``, ``unpack``, ``split_cond`` replaced by :func:`slurmjobs.Grid`
    - ``singularity_command`` replaced by :func:`slurmjobs.Singularity`
    - ``Factory`` replaced by :func:`slurmjobs.util.subclass_lookup`

 - :func:`slurmjobs.util.flatten` now returns a generator rather than a list.

 - ``slurmjobs.Jobs.template`` and ``slurmjobs.Jobs.run_template`` both expect a template string (not a path).
   to specify a path, either have a way to read it from file or just extend the template
 - simplified argument formatting (removed special namedtuple classes)

    - changed ``NoArgVal`` to just ``...``
    - changed ``Argument.build`` to just ``Argument.__call__``
 - improved how command, cli, and args are rendered (all done in jinja now)
 - added overridable method ``Receipt.hash_args`` to allow for custom hashing
 - added proper docs
 - added tensorflow ``2.7`` to ``cuda_versions.csv``
 - added ``scripts/singuconda`` and ``slurmjobs.singuconda`` as a WIP rewrite.


0.2.2
-------

 - `cmd_wrapper` can also be a function
 - added `util.find_tensorflow_cuda_version` to lookup cuda versions
 - `util.singularity_command` returns a function that will now escape quotes in the passed command

0.2.1
-------

 - Now you can pass in a list of dicts and it will use each dictionary as a job. This works along side the parameter grid expansion so you can do:
   ```python
   jobs.generate([{'param1': 5}, ('param1', [100, 150]), ('param2', [200, 250])])
   ```
 - Added `cmd_wrapper` argument to `SlurmBatch('python myscript.py', cmd_wrapper=slurmjobs.util.singularity_command(overlay, sif))` for easier command formatting (no longer need to use `multicmd=True` and `{__all__}`). It expects a string with one positional format arg, e.g. ('sudo {}')

0.2.0
-------

Oops - TODO - fill in. This was changes to adapt to NYU Greene and Singularity containers.

0.1.7
-------
 - added JSON metadata that can be stored in the receipt. Currently, adds `duration_secs` and `time`
 - added more receipt logging (on successful write, on skip, on error)
 - Set `slurmjobs.Receipt.TEST` instead of `slurmjobs.use_receipt.TEST`


0.1.2
-------

 - Added a receipt utility to avoid re-running functions `slurmjobs.use_receipt(func)(*a, **kw)`
 - Added `Batch().generate(expand_grid=False)` option to avoid expanding parameters and passing explicit grids
 - fixed json encoding error in run templates
 - 

0.1.1
-------

 - commands can now access the original values (without command line flag attached) by using the variable name preceded with an underscore. e.g.
    - `'{year}' -> '--year 2016'`
    - `'{_year}' -> '2016'`
 - specifying `cli=False` will disable any formatting and will just pass them sequentially.
 - weird things were happening when `shlex.quote`-ing `repr` so changed to `json.dumps`

0.1.0
-------

 - expanded support to handle multi-line commands.
 - added more tests
 - moved `init_script` so it happens after activating conda
 - added `source ~/.bashrc` to job
 - added `run_init_script` so scripts can run code before you submit the jobs
 - removed hard coded `nodes` sbatch arg. It is now changeable (not sure why it was hardcoded..)
