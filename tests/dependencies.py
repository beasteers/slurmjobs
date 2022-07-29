import os.path
import slurmjobs as sj
from slurmjobs.pipeline import PipelineTask, SlurmDependency, SlurmPipeline


grid1 = sj.Grid([('a', [1, 2]), ('b', [3, 4])])

# works
# grid2 = sj.Grid([('c', [1, 2]), ('d', [3, 4])])
# breaks
grid2 = sj.Grid([('c', [1, 2]), ('b', [3, 4])])
# works
grid2 = sj.Grid([('c', [1, 2])])

grid3 = sj.Grid([('f', [1, 2])])

class Task1(PipelineTask):
    pass

class Task2(PipelineTask): 
    def get_dependency_params_iter(self, dependency, name=None):
        if isinstance(dependency.task, Task1):
            for job_id, params, dep_dict in dependency.job_iter():
                orig_params = params
                # Rename/modify parameters
                params = sj.GridItem.as_grid_item({
                    'dep_a': f"{params['a']}",
                    'dep_b': f"{params['b']}",
                })
                yield params, orig_params


class Task3(PipelineTask):
    def get_dependency_params_iter(self, dependency, name=None):
        if isinstance(dependency.task, Task2):
            res_dirs = []
            orig_params_list = []
            for job_id, params, dep_dict in dependency.job_iter():
                res_dirs.append(params['out_dir'])
                orig_params_list.append(params)
            # Reduce the dependencies to a format that the task can use as
            # input, like the directory containing all of the outputs for the
            # dependencies (assuming non-dependencies aren't also outputting there)
            consume_dir = os.path.commonprefix(res_dirs)
            yield sj.GridItem.as_grid_item({'consume_dir': consume_dir}), tuple(orig_params_list)



task1 = Task1(
    jobs=sj.Sing('python mystuff.py train', name='train'),
    out_dir="/path/to/task1/output",
    grid=grid1,
)

task2 = Task2(
    jobs=sj.Sing('python mystuff.py test', name='test'),
    out_dir="/path/to/task2/output",
    grid=grid2,
)

task3 = Task3(
    jobs=sj.Sing('python mystuff.py summarize', name='summarize'),
    out_dir="/path/to/task3/output",
    grid=grid3,
)

task2.add_dependencies({
    'mypreciousdep': SlurmDependency(task=task1)
})

task3.add_dependencies({
    'mybeloveddep': SlurmDependency(task=task2)
})

pipeline = SlurmPipeline('mystuff')
run_script, job_paths = pipeline.generate([task1, task2, task3])
sj.util.summary(run_script, job_paths)
