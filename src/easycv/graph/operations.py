"""Apply CV operations to modify CVData.

This module contains the logic to apply operations (patches) to a CV.
Operations are atomic changes that can be applied in sequence.

The operation system is designed to be extensible:
- Content operations (current): modify text, bullets, entries
- Style operations (future): modify layout, fonts, colors
"""

from copy import deepcopy
from typing import Any

from easycv.graph.state import (
    AddBulletOp,
    CVOperation,
    RemoveBulletOp,
    ReorderSectionsOp,
    UpdateBulletOp,
    UpdateEntryOp,
    UpdateHeaderOp,
    UpdateLabeledItemOp,
    UpdateParagraphOp,
    UpdateSectionHeadingOp,
    UpdateTagsOp,
)
from easycv.schemas import CVData
from easycv.schemas.cv_model import Bullet


class OperationError(Exception):
    """Raised when an operation cannot be applied."""


def apply_operations(cv: CVData, operations: list[CVOperation]) -> CVData:
    """Apply a list of operations to a CV, returning a new CVData.

    Args:
        cv: The current CV data.
        operations: List of operations to apply in sequence.

    Returns:
        A new CVData with all operations applied.

    Raises:
        OperationError: If an operation is invalid or cannot be applied.
    """
    # Work on a deep copy to avoid mutating the original
    result = cv.model_copy(deep=True)

    for op in operations:
        result = _apply_single_operation(result, op)

    return result


def _apply_single_operation(cv: CVData, op: CVOperation) -> CVData:
    """Apply a single operation to the CV."""
    match op.op:
        case "update_header":
            return _apply_update_header(cv, op)
        case "update_bullet":
            return _apply_update_bullet(cv, op)
        case "add_bullet":
            return _apply_add_bullet(cv, op)
        case "remove_bullet":
            return _apply_remove_bullet(cv, op)
        case "update_entry":
            return _apply_update_entry(cv, op)
        case "update_tags":
            return _apply_update_tags(cv, op)
        case "update_labeled_item":
            return _apply_update_labeled_item(cv, op)
        case "update_paragraph":
            return _apply_update_paragraph(cv, op)
        case "update_section_heading":
            return _apply_update_section_heading(cv, op)
        case "reorder_sections":
            return _apply_reorder_sections(cv, op)
        case _:
            raise OperationError(f"Unknown operation type: {op.op}")


def _apply_update_header(cv: CVData, op: UpdateHeaderOp) -> CVData:
    """Update a header field."""
    header_dict = cv.header.model_dump()
    header_dict[op.field] = op.value
    return cv.model_copy(update={"header": header_dict})


def _apply_update_bullet(cv: CVData, op: UpdateBulletOp) -> CVData:
    """Update a bullet's text."""
    _validate_entry_path(cv, op.section_index, op.entry_index)
    section = cv.sections[op.section_index]

    if section.content.layout != "entries":
        raise OperationError(f"Section {op.section_index} is not an entries layout")

    entries = deepcopy(section.content.entries)
    entry = entries[op.entry_index]

    if op.bullet_index >= len(entry.bullets):
        raise OperationError(
            f"Bullet index {op.bullet_index} out of range for entry with {len(entry.bullets)} bullets"
        )

    entry.bullets[op.bullet_index] = Bullet(
        text=op.new_text,
        url=entry.bullets[op.bullet_index].url,
        children=entry.bullets[op.bullet_index].children,
    )

    return _update_section_entries(cv, op.section_index, entries)


def _apply_add_bullet(cv: CVData, op: AddBulletOp) -> CVData:
    """Add a new bullet to an entry."""
    _validate_entry_path(cv, op.section_index, op.entry_index)
    section = cv.sections[op.section_index]

    if section.content.layout != "entries":
        raise OperationError(f"Section {op.section_index} is not an entries layout")

    entries = deepcopy(section.content.entries)
    entry = entries[op.entry_index]

    new_bullet = Bullet(text=op.text)

    if op.position is None:
        entry.bullets.append(new_bullet)
    else:
        entry.bullets.insert(op.position, new_bullet)

    return _update_section_entries(cv, op.section_index, entries)


def _apply_remove_bullet(cv: CVData, op: RemoveBulletOp) -> CVData:
    """Remove a bullet from an entry."""
    _validate_entry_path(cv, op.section_index, op.entry_index)
    section = cv.sections[op.section_index]

    if section.content.layout != "entries":
        raise OperationError(f"Section {op.section_index} is not an entries layout")

    entries = deepcopy(section.content.entries)
    entry = entries[op.entry_index]

    if op.bullet_index >= len(entry.bullets):
        raise OperationError(
            f"Bullet index {op.bullet_index} out of range for entry with {len(entry.bullets)} bullets"
        )

    entry.bullets.pop(op.bullet_index)

    return _update_section_entries(cv, op.section_index, entries)


def _apply_update_entry(cv: CVData, op: UpdateEntryOp) -> CVData:
    """Update an entry's metadata."""
    _validate_entry_path(cv, op.section_index, op.entry_index)
    section = cv.sections[op.section_index]

    if section.content.layout != "entries":
        raise OperationError(f"Section {op.section_index} is not an entries layout")

    entries = deepcopy(section.content.entries)
    entry_dict = entries[op.entry_index].model_dump()
    entry_dict[op.field] = op.value
    entries[op.entry_index] = type(entries[op.entry_index]).model_validate(entry_dict)

    return _update_section_entries(cv, op.section_index, entries)


def _apply_update_tags(cv: CVData, op: UpdateTagsOp) -> CVData:
    """Update an entry's tags."""
    _validate_entry_path(cv, op.section_index, op.entry_index)
    section = cv.sections[op.section_index]

    if section.content.layout != "entries":
        raise OperationError(f"Section {op.section_index} is not an entries layout")

    entries = deepcopy(section.content.entries)
    entries[op.entry_index].tags = op.tags

    return _update_section_entries(cv, op.section_index, entries)


def _apply_update_labeled_item(cv: CVData, op: UpdateLabeledItemOp) -> CVData:
    """Update a labeled item in a labeled_list section."""
    _validate_section_index(cv, op.section_index)
    section = cv.sections[op.section_index]

    if section.content.layout != "labeled_list":
        raise OperationError(f"Section {op.section_index} is not a labeled_list layout")

    items = deepcopy(section.content.items)

    if op.item_index >= len(items):
        raise OperationError(
            f"Item index {op.item_index} out of range for section with {len(items)} items"
        )

    item = items[op.item_index]
    if op.label is not None:
        item.label = op.label
    if op.values is not None:
        item.values = op.values

    sections = deepcopy(cv.sections)
    content_dict = section.content.model_dump()
    content_dict["items"] = [i.model_dump() for i in items]
    sections[op.section_index] = section.model_copy(
        update={"content": type(section.content).model_validate(content_dict)}
    )

    return cv.model_copy(update={"sections": sections})


def _apply_update_paragraph(cv: CVData, op: UpdateParagraphOp) -> CVData:
    """Update a paragraph section's text."""
    _validate_section_index(cv, op.section_index)
    section = cv.sections[op.section_index]

    if section.content.layout != "paragraph":
        raise OperationError(f"Section {op.section_index} is not a paragraph layout")

    sections = deepcopy(cv.sections)
    content_dict = section.content.model_dump()
    content_dict["text"] = op.text
    sections[op.section_index] = section.model_copy(
        update={"content": type(section.content).model_validate(content_dict)}
    )

    return cv.model_copy(update={"sections": sections})


def _apply_update_section_heading(cv: CVData, op: UpdateSectionHeadingOp) -> CVData:
    """Update a section's heading."""
    _validate_section_index(cv, op.section_index)

    sections = deepcopy(cv.sections)
    sections[op.section_index] = sections[op.section_index].model_copy(
        update={"heading": op.heading}
    )

    return cv.model_copy(update={"sections": sections})


def _apply_reorder_sections(cv: CVData, op: ReorderSectionsOp) -> CVData:
    """Reorder sections."""
    if sorted(op.new_order) != list(range(len(cv.sections))):
        raise OperationError(
            f"Invalid section order: {op.new_order}. "
            f"Must be a permutation of [0, {len(cv.sections) - 1}]"
        )

    sections = [cv.sections[i] for i in op.new_order]
    return cv.model_copy(update={"sections": sections})


# =============================================================================
# Helpers
# =============================================================================


def _validate_section_index(cv: CVData, section_index: int) -> None:
    """Validate that section_index is in range."""
    if section_index >= len(cv.sections):
        raise OperationError(
            f"Section index {section_index} out of range for CV with {len(cv.sections)} sections"
        )


def _validate_entry_path(cv: CVData, section_index: int, entry_index: int) -> None:
    """Validate that section and entry indices are in range."""
    _validate_section_index(cv, section_index)
    section = cv.sections[section_index]

    if section.content.layout != "entries":
        raise OperationError(f"Section {section_index} is not an entries layout")

    entries = section.content.entries
    if entry_index >= len(entries):
        raise OperationError(
            f"Entry index {entry_index} out of range for section with {len(entries)} entries"
        )


def _update_section_entries(cv: CVData, section_index: int, entries: list[Any]) -> CVData:
    """Helper to update a section's entries."""
    sections = deepcopy(cv.sections)
    section = sections[section_index]
    content_dict = section.content.model_dump()
    content_dict["entries"] = [e.model_dump() for e in entries]
    sections[section_index] = section.model_copy(
        update={"content": type(section.content).model_validate(content_dict)}
    )
    return cv.model_copy(update={"sections": sections})
