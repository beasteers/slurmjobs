from slurmjobs import SlurmBatch

batch = SlurmBatch(
    'python train.py', email='me@something.com',
    conda_env='my_env', sbatch_dir='sample')

# generate scripts
run_script, job_paths = batch.generate([
    ('kernel_size', [2, 3, 5]),
    ('lr', [1e-4, 1e-3]),
], dataset='audioset')



batch = SlurmBatch(
    'python train.py',
    email='me@something.com',
    conda_env='my_env')

# generate scripts across parameter grid
run_script, job_paths = batch.generate([
    ('kernel_size', [2, 3, 5]),
    ('nb_stacks', [1, 2]),
    ('lr', [1e-4, 1e-3]),
], receptive_field=6)

print('I just generated', len(job_paths), 'job scripts:')
for p in job_paths:
    print('\t', p)
print()

print('To submit all jobs, run:')
print('.', run_script)
print()
