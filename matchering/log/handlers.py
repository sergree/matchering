# -*- coding: utf-8 -*-

"""
Matchering - Audio Matching and Mastering Python Library
Copyright (C) 2016-2021 Sergree

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from .explanations import get_explanation_handler


class __LogHandlers:
    @staticmethod
    def __dummy(*args, **kwargs):
        pass

    warning_handler = __dummy
    info_handler = __dummy
    debug_handler = __dummy
    explanation_handler = __dummy

    @staticmethod
    def __check_empty(explicit_handler, default_handler):
        return explicit_handler if explicit_handler else default_handler

    @classmethod
    def set_handlers(
        cls,
        default_handler=None,
        warning_handler=None,
        info_handler=None,
        debug_handler=None,
        show_codes=False,
    ):
        default_handler = cls.__check_empty(default_handler, cls.__dummy)
        cls.warning_handler = cls.__check_empty(warning_handler, default_handler)
        cls.info_handler = cls.__check_empty(info_handler, default_handler)
        cls.debug_handler = cls.__check_empty(debug_handler, default_handler)
        cls.explanation_handler = get_explanation_handler(show_codes=show_codes)


def set_handlers(
    default_handler=None,
    warning_handler=None,
    info_handler=None,
    debug_handler=None,
    show_codes=False,
):
    __LogHandlers.set_handlers(
        default_handler=default_handler,
        warning_handler=warning_handler,
        info_handler=info_handler,
        debug_handler=debug_handler,
        show_codes=show_codes,
    )


def warning(*args, **kwargs):
    __LogHandlers.warning_handler(__LogHandlers.explanation_handler(*args, **kwargs))


def info(*args, **kwargs):
    __LogHandlers.info_handler(__LogHandlers.explanation_handler(*args, **kwargs))


def debug(*args, **kwargs):
    __LogHandlers.debug_handler(*args, **kwargs)


def debug_line():
    debug("-" * 40)
