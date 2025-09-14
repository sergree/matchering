"""
Core Matchering algorithm implementation.
"""

from .analyzer import FrequencyAnalyzer
from .matcher import AudioMatcher
from .processor import AudioProcessor

__all__ = ['FrequencyAnalyzer', 'AudioMatcher', 'AudioProcessor']