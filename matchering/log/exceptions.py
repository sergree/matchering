from .explanations import get_explanation_handler
from .codes import Code


class ModuleError(Exception):
    def __init__(self, code: Code):
        Exception.__init__(self, get_explanation_handler(show_codes=True)(code))
