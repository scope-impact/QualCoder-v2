"""Coding dialogs."""

from src.contexts.coding.presentation.dialogs.auto_code_dialog import AutoCodeDialog
from src.contexts.coding.presentation.dialogs.code_suggestion_dialog import (
    CodeSuggestionDialog,
)
from src.contexts.coding.presentation.dialogs.color_picker_dialog import (
    ColorPickerDialog,
)
from src.contexts.coding.presentation.dialogs.create_category_dialog import (
    CreateCategoryDialog,
)
from src.contexts.coding.presentation.dialogs.create_code_dialog import CreateCodeDialog
from src.contexts.coding.presentation.dialogs.delete_code_dialog import DeleteCodeDialog
from src.contexts.coding.presentation.dialogs.duplicate_codes_dialog import (
    DuplicateCodesDialog,
)
from src.contexts.coding.presentation.dialogs.memo_dialog import MemoDialog

__all__ = [
    "AutoCodeDialog",
    "CodeSuggestionDialog",
    "ColorPickerDialog",
    "CreateCategoryDialog",
    "CreateCodeDialog",
    "DeleteCodeDialog",
    "DuplicateCodesDialog",
    "MemoDialog",
]
