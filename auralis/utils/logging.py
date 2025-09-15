# -*- coding: utf-8 -*-

"""
Auralis Logging System
~~~~~~~~~~~~~~~~~~~~~~

Logging and debug utilities

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.

Refactored from Matchering 2.0 by Sergree and contributors
"""


class Code:
    """Log message codes"""
    INFO_LOADING = "Loading audio files..."
    INFO_EXPORTING = "Exporting results..."
    INFO_COMPLETED = "Processing completed successfully"
    ERROR_VALIDATION = "Validation error"


class ModuleError(Exception):
    """Custom exception for module errors"""
    def __init__(self, code):
        self.code = code
        super().__init__(f"Module error: {code}")


# Global log handler
_log_handler = None


def set_log_handler(handler):
    """Set the global log handler function"""
    global _log_handler
    _log_handler = handler


def debug(message: str):
    """Log a debug message"""
    if _log_handler:
        _log_handler(f"DEBUG: {message}")


def info(message: str):
    """Log an info message"""
    if _log_handler:
        _log_handler(f"INFO: {message}")


def warning(message: str):
    """Log a warning message"""
    if _log_handler:
        _log_handler(f"WARNING: {message}")


def error(message: str):
    """Log an error message"""
    if _log_handler:
        _log_handler(f"ERROR: {message}")


def debug_line():
    """Log a debug separator line"""
    if _log_handler:
        _log_handler("-" * 50)