"""In-memory saved-designs cache. POST to upsert, GET to list.

Lives only for the lifetime of the running process — there's no database
here, just a session-scoped cache, matching the original behaviour."""

import random
from typing import List, Optional

from fastapi import APIRouter, Body

router = APIRouter()

_local_saved: List[dict] = []


@router.post("/api/save-design")
def save_design(design: dict = Body(...)) -> dict:
    if "id" not in design or not design["id"]:
        design["id"] = f"vel-{random.randint(100000, 999999)}"

    for i, item in enumerate(_local_saved):
        if item.get("id") == design["id"]:
            _local_saved[i] = design
            return {"success": True, "id": design["id"], "totalCount": len(_local_saved)}

    _local_saved.append(design)
    return {"success": True, "id": design["id"], "totalCount": len(_local_saved)}


@router.get("/api/saved-designs")
def get_saved_designs() -> List[dict]:
    return _local_saved


# ---------------------------------------------------------------------------
# Storage helper functions (for use by other modules)
# ---------------------------------------------------------------------------

def get_design_by_id(design_id: str) -> Optional[dict]:
    """
    Retrieve a saved design by its ID.
    Returns None if not found.
    
    Used by the PDF export endpoint to fetch designs.
    """
    for design in _local_saved:
        if design.get("id") == design_id:
            return design
    return None


def get_all_designs() -> List[dict]:
    """Get all saved designs."""
    return _local_saved


def delete_design(design_id: str) -> bool:
    """
    Delete a design by ID.
    Returns True if deleted, False if not found.
    """
    for i, design in enumerate(_local_saved):
        if design.get("id") == design_id:
            _local_saved.pop(i)
            return True
    return False


def clear_all_designs() -> None:
    """Clear all saved designs (useful for testing)."""
    _local_saved.clear()
