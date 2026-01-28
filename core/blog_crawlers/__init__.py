"""
Blog crawlers module
"""

from .kdnuggets import build_blog_index_node as build_kdnuggets_index
from .analytics_vidhya import build_analytics_vidhya_index
from .machine_learning_mastery import build_machine_learning_mastery_index

__all__ = [
    'build_kdnuggets_index',
    'build_analytics_vidhya_index',
    'build_machine_learning_mastery_index'
]
