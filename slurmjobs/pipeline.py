import itertools
import time
import pathtrees
from typing import List, Dict, Union, Optional
from copy import deepcopy
from toposort import toposort
from . import util
from .core import Jobs, env
from .grid import BaseGrid, GridItem, GridItemBundle


class PipelineTask:
    allowed_job_id_chars: str = '_'
    special_character_replacement: str = '_'

    def __init__(self,
        jobs: Jobs, grid: BaseGrid, *a,
        name: Optional[str] = None,
        ignore_job_id_keys: Optional[List[str]] = None,
        dependencies: Optional[Union[List[Dependency], Dict[str, Dependency]]] = None, **kw
    ):
        # Basically wraps the arguments that would be passed to jobs.generate()
        self.jobs = jobs
        self.grid = grid
        self.a = a
        self.ignore_job_id_keys = ignore_job_id_keys
        self.kw = kw
        # If no name is provided, use the same name as the jobs object
        self.name = name or jobs.name
        self.dependencies = self._preprocess_dependencies(dependencies)

    def _preprocess_dependencies(self, dependencies):
        """Override for custom dependency organization or validation"""
        if isinstance(dependencies, List):
            dependencies = {d.name for d in dependencies}
        else:
            dependencies = dependencies or {}
        return dependencies

    def add_dependencies(self, dependencies, overwrite=False):
        dependencies = self._preprocess_dependencies(dependencies)
        for k, v in dependencies.items():
            if not overwrite and k in self._dependencies:
                raise ValueError(f"Trying to add dependency with name '{k}', "
                                    "but it already exists")
            self.dependencies[k] = v

    def get_job_id(self, params: GridItem):
        # let job itself take care of the job ID, the dependent params are
        # assumed to be passed
        _job_id = self.jobs.format_job_id(
            params,
            params.grid_keys,
            name=self.name,
            ignore_keys=self.ignore_job_id_keys
        )
        job_id = _job_id.strip()
        # sanitize job_id so we can use them as environment variables
        job_id = ''.join(
            c if c in self.allowed_job_id_chars or c.isalnum() else self.special_character_replacement
            for c in job_id
        )
        if job_id[0].isnumeric():
            raise ValueError('Pipeline Job ID cannot begin with a number ({_job_id})')

        return job_id

    def get_dependency_params_iter(self, dependency, name=None):
        """ Override if you want to do anything specific to the params
            before returning them or handle different kinds of dependencies
            differently"""
        for job_id, params, dep_dict in dependency.job_iter():
            orig_params = params
            yield params, orig_params

    def get_dependency_job_ids(self):
        return [
            job_id
            for dep in self.dependencies.values()
            for job_id in dep.get_all_job_ids()
        ]

    def get_all_job_ids(self, grid=None):
        return [job_id for job_id, _, _ in self.job_iter(grid=grid)]

    def job_iter(self, grid=None):
        """ Yield the params for each grid item"""
        grid = grid or self.grid
        dep_list, dep_param_grid_iters, orig_dep_param_grid_iters = zip(*[
            (dep,) + self.get_dependency_params_iter(dep, name=name)
            for name, dep in self.dependencies.items()
        ])

        for grid_item in grid:
            for dep_param_grids, orig_dep_param_grids in zip(
                itertools.product(*dep_param_grid_iters),
                itertools.product(*orig_dep_param_grid_iters)
            ):
                params = GridItemBundle(grid_item, *dep_param_grids)
                params.positional += self.a
                params.update(self.kw)

                job_id = self.get_job_id(params)

                dependency_job_dict = {}
                for dep, dep_grid_item in zip(dep_list, orig_dep_param_grids):
                    if dep.done_condition not in dependency_job_dict:
                        dependency_job_dict[dep.done_condition] = []
                    dep_job_id = dep.get_job_id(dep_grid_item)
                    dependency_job_dict[dep.done_condition].append(dep_job_id)

                yield (job_id, params, dependency_job_dict)


class Dependency:
    def __init__(self,
        task: PipelineTask,
        done_condition: str,
        reduce: bool = False,
        dependency_grid: Optional[BaseGrid] = None,
    ):
        self.task = task
        done_condition = done_condition.lower()
        self.validate_terminate_condition(done_condition)
        self.done_condition = done_condition
        # reduce: if True, all job instances are dependencies, otherwise
        # corresponds to a single instance of the dependency, instance
        self.reduce = reduce
        # dependency_grid: Specifies subset of dependency grid that these jobs
        # can depend on. None is meant to imply that these jobs can depend on
        # the full Grid used by the dependency. If reduce = True, each instance
        # of these jobs requires all instances of the dependency, otherwise, it
        # requires only one instance
        dependency_grid = self.task.jobs.get_valid_grid(
            dependency_grid or self.task.grid
        )
        self.validate_dependency_grid(dependency_grid)
        self.dependency_grid = dependency_grid

    @property
    def name(self):
        return self.task.name

    def validate_terminate_condition(self, done_condition: str):
        """Override to perform validation on the conditions"""
        if done_condition not in ('completed', 'failed', 'timeout'):
            raise ValueError(f'done_condition = {done_condition} is invalid')

    def validate_dependency_grid(self, dependency_grid: Optional[BaseGrid]):
        """Override to perform validation on the dependency grid"""
        # TODO: check if grid is a subset of dependencies
        # self.task
        pass

    def get_job_id(self, grid_item: GridItem):
        return self.task.get_job_id(grid_item)

    def job_iter(self):
        for res in self.task.job_iter(grid=self.dependency_grid):
            yield res

    def get_all_job_ids(self):
        return [job_id for job_id, _, _ in self.job_iter()]


class Pipeline:
    """ Pipeline object for creating pipelines """

    run_template = '''{% extends 'run_pipeline.base.j2' %}
    '''

    def __init__(self, name):
        self.name = name
        self.paths = self.get_paths()

    def get_paths(self, **kw):
        paths = pathtrees.tree(self.root_dir, {'{name}': {
            'run.sh': 'run',
            'time_generated': 'time_generated',
        }}).update(name=self.name, **kw)
        return paths

    def validate_task(self,
        task: PipelineTask,
        task_dict: Optional[Dict[str, PipelineTask]] = None
    ):
        # make sure name is specified
        if not task.name:
            raise ValueError(
                "A unique name must be provided for each PipelineTask "
                "object to use with a Pipeline"
            )

        # make sure we don't have different Jobs objects with the same name
        if task_dict and task.name in task_dict:
            if task != task_dict[task.name]:
                raise ValueError(
                    f"Found different PipelineTask objects with the same name "
                    f"({task.name}). PipelineTask names must be unique."
                )

    def get_task_grid_item(self, task: PipelineTask, grid_item):
        grid_item = deepcopy(grid_item)
        grid_item.positional += task.a
        grid_item.update(task.kw)
        return grid_item

    def generate(self, tasks: List[PipelineTask]):
        # get jobs, params, and dependencies
        job_dict = {}
        for task in tasks:
            for job_id, params, dependencies in task.job_iter():
                # Make sure job_id doesn't already exist
                if job_id in job_dict:
                    raise RuntimeError(f"Duplicate job ID: {job_id}")
                job_dict[job_id] = (task, params, dependencies)

        # generate job files
        job_path_dict = {
            task.jobs.generate_job(job_id, _grid=task.grid, _args=params)
            for job_id, (task, params, _) in job_dict.items()
        }
        
        # get dependency map
        dependencies = {
            job_id: deps for job_id, (_, _, deps) in job_dict.items()
        }

        # sort jobs topologically to get linearized groupings of jobs
        dependency_graph = {
            job_id: set([d for lst in deps.values() for d in lst])
            for job_id, deps in dependencies.items()
        }
        job_groups = list(toposort(dependency_graph))

        # generate run file
        run_script = self.generate_run_script(
            job_groups, job_path_dict, dependencies
        )

        # store the current timestamp
        if 'time_generated' in self.paths.paths:
            self.paths.time_generated.write_text(str(time.time()))

        # create linear list of jobs to return
        job_paths_list = [
            job_path_dict[job_id]
            for group in job_groups
            for job_id in group
        ]
        return run_script, job_paths_list
    

    def generate_run_script(self, _job_groups, _job_id_to_path, _dependencies, **kw):
        """Generate a job run script that will submit all jobs."""
        # generate run script
        file_path = self.paths.run
        with open(file_path, "w") as f:
            f.write(env.from_string(self.run_template).render(
                name=self.name,
                job_groups=_job_groups,
                job_id_to_path=_job_id_to_path,
                paths=self.paths,
                dependencies=_dependencies, **kw))
        util.make_executable(file_path)
        return file_path


class ParallelPipeline(Pipeline):
    """ Pipeline object for creating pipelines where job groups are run in parallel """

    run_template: str = '''{% extends 'run_pipeline.parallel.j2' %}
    '''


class SlurmPipeline(Pipeline):
    """ Pipeline object for creating pipelines where job groups are run in parallel """
    run_template: str = '''{% extends 'run_pipeline.slurm.j2' %}
    '''
