from .log.handlers import set_handlers as log
from .results import Result, pcm16, pcm24
from .defaults import Config
from .core import process
from .loader import load
from .checker import check

__title__ = 'matchering'

__author__ = 'sergree'
__credits__ = ['Sergey Grishakov', 'Igor Isaev', 'Chin Yun Yu']
__maintainer__ = 'sergree'
__email__ = 'wokashi.rg@gmail.com'
__license__ = 'GPL'
__copyright__ = 'Copyright 2016-2020, sergree'

__version__ = '2.0.0rc1'
__status__ = 'Development'
