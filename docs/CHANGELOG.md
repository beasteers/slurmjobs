# Changes

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
