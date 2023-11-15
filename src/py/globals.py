from typing import Optional
from collections.abc import Sequence
import ifcopenshell


_live_editing: bool = True
_ifc_model: Optional[ifcopenshell.file] = None
_entities_to_ignore: Optional[list[ifcopenshell.entity_instance]] = None
_ifc_classes_to_ignore: Optional[Sequence[str]] = None
_hook_running: bool = False
