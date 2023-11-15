import sys
import ast
import types
from typing import Callable, Optional, Any
from collections.abc import Sequence
from functools import partial
import ifcopenshell


def entities_to_remove(
        ifc_model: ifcopenshell.file,
        element: ifcopenshell.entity_instance,
        entities_to_also_consider: Optional[
            Sequence[ifcopenshell.entity_instance]] = None,
        entities_to_ignore: Optional[
            Sequence[ifcopenshell.entity_instance]] = None,
        ifc_classes_to_ignore: Optional[Sequence[str]] = None
) -> tuple[
    set[ifcopenshell.entity_instance], list[ifcopenshell.entity_instance]
]:
    entities_to_also_consider = entities_to_also_consider or []
    entities_to_ignore = entities_to_ignore or []
    ifc_classes_to_ignore = ifc_classes_to_ignore or []
    to_delete: set = set([element])
    subgraph: list = list(ifc_model.traverse(element, breadth_first=True))
    subgraph.extend(entities_to_also_consider)
    subgraph_set: set = set(subgraph)
    subelement_queue: list = ifc_model.traverse(element, max_levels=1)
    while subelement_queue:
        subelement: ifcopenshell.entity_instance = subelement_queue.pop(0)
        if (
                subelement.id()
                and subelement not in entities_to_ignore
                and not any([
                    subelement.is_a(ifc_class)
                    for ifc_class in ifc_classes_to_ignore
                ])
                and len(set(ifc_model.get_inverse(subelement)) - subgraph_set) == 0
        ):
            to_delete.add(subelement)
            subelement_queue.extend(ifc_model.traverse(subelement, max_levels=1)[1:])
    return to_delete, subgraph


def remove_entities(ifc_model: ifcopenshell.file, entities: set, subgraph: list) -> None:
    for subelement in filter(lambda e: e in entities, subgraph[::-1]):
        try:
            ifc_model.remove(subelement)
        except RuntimeError:
            eid, etype = subelement.id(), subelement.is_a()
            print(f'Attempting to delete non-existant entity #{eid}/{etype}')


def remove_references_to_entities(entities: set, module: types.ModuleType) -> None:
    for namespace_name, namespace_var in module.__dict__.items():
        if isinstance(namespace_var, ifcopenshell.entity_instance) and namespace_var in entities:
            module.__dict__[namespace_name] = None


class NoLiveEditing:
    def __enter__(self):
        global _live_editing
        _live_editing = False

    def __exit__(self, exc_type, exc_value, exc_traceback):
        global _live_editing
        _live_editing = True


def ios_entity_overwrite_hook(module: types.ModuleType) -> Callable:
    """Audit hook to remove ifcopenshell entities from an IFC model on
    overwriting"""

    global _ifc_model
    global _entities_to_ignore
    global _ifc_classes_to_ignore

    def remove_entity_subgraph_previous_references(
        variable_name: str, entity: ifcopenshell.entity_instance
    ) -> None:
        entity_type: str = entity.is_a()
        entity_id: int = entity.id()
        to_delete, subgraph = entities_to_remove(
            _ifc_model, entity, entities_to_ignore=_entities_to_ignore,
            ifc_classes_to_ignore=_ifc_classes_to_ignore
            )
        with NoLiveEditing():
            remove_references_to_entities(to_delete, module)
        remove_entities(_ifc_model, to_delete, subgraph)
        txt_base = f'Variable "{variable_name}", '
        txt_base += f'containing #{entity_id}/{entity_type} '
        num_deleted = len(to_delete) - 1
        if num_deleted == 0:
            txt_detail = 'was overwritten'
        else:
            txt_detail = f'(+{num_deleted} other fully dependent '
            txt_detail += 'entity' if num_deleted == 1 else 'entities'
            txt_detail += ') were overwritten'
        print(f'{txt_base}{txt_detail}')

    def remove_ifc_model(variable_name: str) -> None:
        all_entities, subgraph = set(), []
        for idx in range(1, _ifc_model.getMaxId() + 1):
            try:
                all_entities.add(_ifc_model.by_id(idx))
            except RuntimeError:
                pass

        num_entities = len(all_entities)
        with NoLiveEditing():
            remove_references_to_entities(all_entities, module)
            remove_entities(_ifc_model, all_entities, subgraph)
            hex_id = hex(id(module.__dict__[variable_name]))
            print(
              f'Overwriting IFC model at {hex_id} with {num_entities} entities'
            )
            module.__dict__[variable_name] = None

    def _hook(event: str, args: tuple) -> None:
        if event != 'compile' or not args:
            return
        ast_module: Any = args[0]
        if not isinstance(ast_module, ast.Module):
            return
        for token in ast_module.body:
            if not isinstance(token, ast.Assign):
                continue
            target: Any = token.targets[0]
            if not isinstance(target, ast.Name):
                continue
            variable_name: str = target.id
            if variable_name not in module.__dict__:
                continue
            variable: Any = module.__dict__[variable_name]
            global _live_editing
            if isinstance(variable, ifcopenshell.file) and _live_editing:
                remove_ifc_model(variable_name)
                continue
            if not isinstance(variable, ifcopenshell.entity_instance):
                continue
            if not _live_editing:
                continue
            remove_entity_subgraph_previous_references(variable_name, variable)

    return _hook


def _download_ifc_model(ifc_model: ifcopenshell.file, filename: str) -> None:
  from google.colab import files
  ifc_model.write(filename)
  files.download(filename)


def enable_live_editing(
    ifc_model: ifcopenshell.file,
    entities_to_ignore: Optional[list[ifcopenshell.entity_instance]] = None,
    ifc_classes_to_ignore: Sequence[str] = (
        'IfcContext', 'IfcRepresentationContext'
    )
) -> None:
    global _ifc_model
    global _entities_to_ignore
    global _ifc_classes_to_ignore
    global _hook_running

    _ifc_model = ifc_model
    _entities_to_ignore = entities_to_ignore
    _ifc_classes_to_ignore = ifc_classes_to_ignore

    # audit hooks cannot be removed (PEP 578)
    # so we register it once and only update globals on further calls

    ifc_model.show = partial(_show_ifc, ifc_model)
    ifc_model.download_as = partial(_download_ifc_model, ifc_model)

    if not _hook_running:
        sys.addaudithook(ios_entity_overwrite_hook(sys.modules[__name__]))
        _hook_running = True
