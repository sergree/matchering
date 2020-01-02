from matchering.log.transcript import get_handler


class ModuleError(Exception):
    def __init__(self, code):
        Exception.__init__(self, get_handler(show_codes=True)(code))
