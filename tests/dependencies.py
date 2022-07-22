import slurmjobs as sj
from slurmjobs.pipeline import PipelineTask, SlurmDependency, SlurmPipeline


grid1 = sj.Grid([('a', [1, 2]), ('b', [3, 4])])

# works
# grid2 = sj.Grid([('c', [1, 2]), ('d', [3, 4])])
# breaks
grid2 = sj.Grid([('c', [1, 2]), ('b', [3, 4])])
# works
grid2 = sj.Grid([('c', [1, 2])])


task1 = PipelineTask(
    jobs=sj.Sing('python mystuff.py train', name='train'),
    grid=grid1,
)
task2 = PipelineTask(
    jobs=sj.Sing('python mystuff.py test', name='test'),
    grid=grid2,
)
task2.add_dependencies({
    'mydep': SlurmDependency(task=task1)
})

pipeline = SlurmPipeline('mystuff')
run_script, job_paths = pipeline.generate([task1, task2])
sj.util.summary(run_script, job_paths)
