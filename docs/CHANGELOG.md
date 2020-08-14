# Changes

## v0.1.0
 - expanded support to handle multi-line commands.
 - added more tests
 - moved `init_script` so it happens after activating conda
 - added `source ~/.bashrc` to job
 - added `run_init_script` so scripts can run code before you submit the jobs
 - removed hard coded `nodes` sbatch arg. It is now changeable (not sure why it was hardcoded..)
