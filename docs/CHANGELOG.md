# Changes

## 0.2.2
 - `cmd_wrapper` can also be a function
 - added `util.find_tensorflow_cuda_version` to lookup cuda versions
 - `util.singularity_command` returns a function that will now escape quotes in the passed command

## 0.2.1
 - Now you can pass in a list of dicts and it will use each dictionary as a job. This works along side the parameter grid expansion so you can do:
   ```python
   jobs.generate([{'param1': 5}, ('param1', [100, 150]), ('param2', [200, 250])])
   ```
 - Added `cmd_wrapper` argument to `SlurmBatch('python myscript.py', cmd_wrapper=slurmjobs.util.singularity_command(overlay, sif))` for easier command formatting (no longer need to use `multicmd=True` and `{__all__}`). It expects a string with one positional format arg, e.g. ('sudo {}')

## 0.2.0
Oops - TODO - fill in. This was changes to adapt to NYU Greene and Singularity containers.

## v0.1.7
 - added JSON metadata that can be stored in the receipt. Currently, adds `duration_secs` and `time`
 - added more receipt logging (on successful write, on skip, on error)
 - Set `slurmjobs.Receipt.TEST` instead of `slurmjobs.use_receipt.TEST`


## v0.1.2
 - Added a receipt utility to avoid re-running functions `slurmjobs.use_receipt(func)(*a, **kw)`
 - Added `Batch().generate(expand_grid=False)` option to avoid expanding parameters and passing explicit grids
 - fixed json encoding error in run templates
 - 

## v0.1.1
 - commands can now access the original values (without command line flag attached) by using the variable name preceded with an underscore. e.g.
    - `'{year}' -> '--year 2016'`
    - `'{_year}' -> '2016'`
 - specifying `cli=False` will disable any formatting and will just pass them sequentially.
 - weird things were happening when `shlex.quote`-ing `repr` so changed to `json.dumps`

## v0.1.0
 - expanded support to handle multi-line commands.
 - added more tests
 - moved `init_script` so it happens after activating conda
 - added `source ~/.bashrc` to job
 - added `run_init_script` so scripts can run code before you submit the jobs
 - removed hard coded `nodes` sbatch arg. It is now changeable (not sure why it was hardcoded..)
