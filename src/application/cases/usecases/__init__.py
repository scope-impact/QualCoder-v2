"""
Case Use Cases - Functional 5-Step Pattern

Use cases for case management operations:
- create_case: Create a new case
- update_case: Update case metadata
- remove_case: Remove a case
- link_source: Link a source to a case
- unlink_source: Unlink a source from a case
- set_attribute: Set an attribute on a case
"""

from src.application.cases.usecases.create_case import create_case
from src.application.cases.usecases.link_source import link_source_to_case
from src.application.cases.usecases.remove_case import remove_case
from src.application.cases.usecases.set_attribute import set_case_attribute
from src.application.cases.usecases.unlink_source import unlink_source_from_case
from src.application.cases.usecases.update_case import update_case

__all__ = [
    "create_case",
    "update_case",
    "remove_case",
    "link_source_to_case",
    "unlink_source_from_case",
    "set_case_attribute",
]
