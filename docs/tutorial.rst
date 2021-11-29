Tutorial
=========

Let's go through the process of running your code in a singularity 
container. 

Setting up Singularity
-------------------------

First we need to create the overlay that will contain our anaconda
distribution along with any packages we want to install to the environment.

``slurmjobs`` provides a script that will do that for you! Just type:

.. code-block:: bash

    singuconda

And it will ask you for some values. All of which you can mash enter through
if you don't care about them (which will use their defaults). The defaults will 
give you a singularity overlay with an empty conda environment. The prompts give 
you the opportunity to change the overlay and sif file paths, as well as specify
which packages you'd like installed, specified in the form of:

- a pip requirements file: 
   i.e. ``pip install -r ./your/requirements.txt`` - you provide: ``./your/requirements.txt``
- a local python package: a repo directory containing a ``setup.py`` file where your project source lives.
   i.e. ``pip install -e ./your/package`` - you provide: ``./your/package``
- any conda packages that you want to install: conda packages
   i.e. ``conda install numpy librosa`` - you provide: ``numpy librosa``

Once we have that information the script will:

 1. Check if the overlay file already exists. If not, then we copy 
    the overlay file to your current directory.
 2. We then enter the singularity container and install miniconda
 3. Then we install all of the pip/conda stuff you requested to conda

Then you're all set! :) You have a singularity overlay with anaconda and any packages you asked it to install.

.. note::

    If people would prefer, I can also refactor ``singuconda`` into a Python class
    to allow you to configure it with the rest of your slurmjobs code.


Generating Jobs
---------------------

Now let's generate some job scripts!

The simplest configuration you can give is:

.. code-block:: python

    import slurmjobs

    def generate():
        jobs = slurmjobs.Singularity('python project/train.py')

        # generate the jobs, providing a grid of 
        # parameters to generate over.
        run_script, job_paths = jobs.generate([
            # two different model types
            ('model', ['AVE', 'AVOL']),
            # try mono and stereo audio
            ('audio_channels', [1, 2]),
        ], epochs=500)

        # print out a summary of the scripts generated
        slurmjobs.util.summary(run_script, job_paths)

    if __name__ == '__main__':
        import fire
        fire.Fire()

Then you can just generate the jobs by doing:

.. code-block:: bash

    python jobs.py generate

And your files will be found in: ``./jobs/project.train`` (name automatically derived from the command name.)

But you can do a lot more:

.. code-block:: python

    import os
    import slurmjobs

    def generate():
        jobs = slurmjobs.Singularity(
            'python train.py',
            # give the job batch a name
            name='my-train-script',
            # say your script uses hydra, so tell slurmjobs how to format your arguments
            cli='hydra',
            # set the working directory for your script
            root_dir='/scratch/myuser/myproject',
            # disable job backups. By default it'll save them as `~{name}_01` etc.
            backup=False,
            # set the email to whoever generates the jobs (nyu uses your netid 
            # for both email and greene, so you can use $USER to make it easier 
            # with multiple people)
            email=f'{os.getenv("USER")}@nyu.edu',
            # set the number of cpus and gpus to request per job
            n_cpus=2, n_gpus=2,
            # set the requested time (e.g. 2 days)
            time='2-0',
            # disable passing job_id to your script (if your script doesn't accept one)
            job_id=None,  # or change the key: job_id='my_job_id',
            # pass any arbitrary sbatch flags
            # see: https://slurm.schedmd.com/sbatch.html
            sbatch={
                ...
            },
            # you can also pass anything else here and it'll be changeable 
            # in __init__ and available in the templates (e.g. if you extend the templates)
        )

        run_script, job_paths = jobs.generate([
            ('model', ['AVE', 'AVOL']),
            ('audio_channels', [1, 2]),
        ], epochs=500)

        slurmjobs.util.summary(run_script, job_paths)

    if __name__ == '__main__':
        import fire
        fire.Fire()


To add initialization and cleanup code around your command, see :ref:`templates` which will tell you how to add custom code. 


Parameter Grids
--------------------

If you have a simple parameter grid, then you don't really have to think about this,
and you can keep passing your grid like the previous example.

But you may also have a slightly more complex grid you want to try. If that is the case,
then you can do:

.. code-block:: python

    from slurmjobs import Grid, LiteralGrid

    g = Grid([
        ('a', [1, 2]),
        ('b', [1, 2]),
    ], name='train')

    # append two configurations
    g = g + LiteralGrid([{'a': 5, 'b': 5}, {'a': 10, 'b': 10}])

    # create a bigger grid from the product of another grid
    g = g * Grid([
        ('c', [5, 6])
    ], name='dataset')

    # omit a configuration from the grid
    g = g - [{'a': 2, 'b': 1, 'c': 5}]

    # then
    assert list(g) == [
        {'a': 1, 'b': 1, 'c': 5},
        {'a': 1, 'b': 1, 'c': 6},
        {'a': 1, 'b': 2, 'c': 5},
        {'a': 1, 'b': 2, 'c': 6},
        # {'a': 2, 'b': 1, 'c': 5},  omitted
        {'a': 2, 'b': 1, 'c': 6},
        {'a': 2, 'b': 2, 'c': 5},
        {'a': 2, 'b': 2, 'c': 6},
        {'a': 5, 'b': 5, 'c': 5},
        {'a': 5, 'b': 5, 'c': 6},
        {'a': 10, 'b': 10, 'c': 5},
        {'a': 10, 'b': 10, 'c': 6},
    ]

    # Then you can pass the grid like normal

    jobs = slurmjobs.Singularity('python train.py')
    run_script, job_paths = jobs.generate(g, epochs=500)


Breaking Arguments across multiple functions
--------------------------------------------------

Sometimes you may have a situation where your arguments need to be broken 
out across multiple functions. You can do this by naming your grids.

.. code-block:: python

    .. code-block:: python 

    class Singularity(slurmjobs.Singularity):
        # remember to extend a base template
        template = '''{% extends 'job.singularity.j2' %}

    {% block command %}
    {{ command }} {{ cli(args.main, indent=4) }}

    python my_other_script.py {{ cli(args.other, indent=4) }}
    {% endblock %}
        '''

    g = slurmjobs.Grid([
        ('a', [1, 2]),
        ('b', [1, 2]),
    ], name='main')

    g * slurmjobs.Grid([
        ('c', [1, 2]),
        ('d', [1, 2]),
    ], name='other')


Customizing Job IDs
-------------------------

The purpose of a job ID is to give your jobs a pretty name that is 
descriptive of its configuration so you can use it in filenames and 
log files while also being unique between job instances so that they're
not both trying to write to the same place.

Canonically, job IDs are created using this pattern: 
``{key}-{value},{key2}-{value2},...``. This is meant as a naive
but somewhat effective way of encoding the parameters.

But things aren't always that simple. The main cases that I 
see you needing to changing the job ID formatter are:

 - your grid contains a long value like a list or long string
 - your grid contains long float values that you want to shorten
 - your grid contains objects that don't have a nice string representation
   (this would most likely lead to an issue with CLI formatting too, but I digress)
 - your grid contains too many keys and you'd like to abbreviate them
   to avoid hitting filename length limits.

Out of the box we include some levers that you can pull to tweak your 
job ID.

.. code-block:: python

    class Singularity(slurmjobs.Singularity):
        # a dict of abbreviations (full_key -> abbreviated_key)
        key_abbreviations = {}
        # a length to clip the keys to (e.g. 2 would turn model into mo)
        abbreviate_length = None
        # limit the precision on float values (e.g. 3 means 3 decimal places)
        float_precision = None 

But of course, I'm sure you may have other ways you want to do things, so you have 
full liberty to change the job ID generation. Just make sure that your 
job IDs are still unique between jobs!!

.. code-block:: python

    class Singularity(slurmjobs.Singularity):
        # formatting for a single key-value pair.
        # you can return a tuple, string, or None (to exclude)
        def format_id_item(self, k, v):
            # I'm wacky and like my keys backwards
            k = k[::-1]
            # e.g. special formatting for booleans
            if v is True:
                return k
            if v is False:
                return f'not-{k}'
            return k, v

        # formatting the entire job ID. Do what you like!
        def format_job_id(self, args, keys=None, name=None):
            return ','.join(
                [name]*bool(name),
                *[f'{k}-{self.format_id_item(args[k])}' for k in keys or args]
            )

.. _templates:

Customizing your Template
----------------------------

Another thing that you'll probably want to end up doing at some point is 
to add some customization, initialization, or cleanup to your scripts.

Often I will personally add most of that internally in my scripts, but you may 
also prefer to add it with bash.

Here's the block structure in each of the templates:

 - base (``job.base.j2``)
    - ``header``: This has a description of the job and arguments
    - ``body``: This is the main body of the script and wraps around everything. You can use this for 
      top-level initialization / cleanup.

        - ``environment``: load anaconda and your conda environment.
        - ``main``: An empty wrapper around the ``command`` block where you can add script initialization / cleanup
            
            - ``command``: The heart of the script. This is where your script gets passed its arguments.

 - shell  (``job.shell.j2`` extends ``job.base.j2``)
    - ``body`` > ``main``: Calls the main block using ``nohup`` so that your shell jobs can survive
      dropped ssh connections.

 - sbatch (``job.sbatch.j2`` extends ``job.base.j2``)
    - ``header`` > ``arguments``: added sbatch arguments at the beginning of the file.
    - ``body`` > ``modules``: This is where we do ``module purge`` and ``module load cuda`` etc.

 - singularity (``job.singularity.j2`` extends ``job.sbatch.j2``)
    - ``body``: wraps with a singularity call. All of the body is run inside the singularity container


Here's how you can add initialization / cleanup code around your command. Use ``{{ super() }}`` to add back in the parent template's code.

.. code-block:: python 

    class Singularity(slurmjobs.Singularity):
        # remember to extend a base template
        template = '''{% extends 'job.singularity.j2' %}

    {% block main %}

    # initialization
    export SOMETHING=asdfasdfasdf
    mkdir -p my-directory

    {# call the rest of the main block #}
    {{ super() }}

    # some cleanup
    rm -r my-directory

    {% endblock %}
        '''

If you want to add code outside the singularity container, you just need to do:

.. code-block:: python 

    class Singularity(slurmjobs.Singularity):
        # remember to extend a base template
        template = '''{% extends 'job.singularity.j2' %}

    {% block body %}
    export SOMETHING=asdfasdfasdf
    mkdir -p my-directory
    {{ super() }}
    rm -r my-directory
    {% endblock %}
        '''

And if you want to delete a parent's section, just do:

.. code-block:: python 

    class Slurm(slurmjobs.Slurm):
        # remember to extend a base template
        template = '''{% extends 'job.sbatch.j2' %}
    
    {% block modules %}{% endblock %}
        '''

Customizing Argument Formatting
----------------------------------


You can define your own formatter by subclassing :func:`slurmjobs.args.Argument`. If your class 
name ends with ``'Argument'``, you can omit that when passing the cli name. 
This works by gathering subclasses matching the passed string against their 
names. If the class ends with 'Argument', the suffix will be removed. If you 
don't want a class to be available, prefix the name with an underscore.

Example:

.. code-block:: python

    import slurmjobs

    class MyCustomArgument(slurmjobs.args.Argument):
        @classmethod
        def format_arg(cls, k, v=None):
            if v is None:
                return
            # idk do something fancy
            return '..{}@{}'.format(k, cls.format_value(v)) # ..size@10
    
    batch = slurmjobs.SBatch('echo', cli='mycustom')
    print(batch.command, batch.cli(size=10, blah='blorp'))
    # echo ..size@10 ..blah@blorp
