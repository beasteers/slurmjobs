from .__version__ import __version__
from . import args
from .grid import *
from .core import *
from . import util
from .receipt import *


# cute little alias
Sing = Singularity

get_cli = args.Argument.get