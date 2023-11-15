from dataclasses import dataclass, field
from typing import Callable, Optional, Any
import ifcopenshell
import ifcopenshell.api


@dataclass
class IfcOpenShellPythonAPI:
    """Helper class to make use of pythonic notation with the IfcOpenShell API
    standard use:
      ifcopenshell.api.run('root.create_entity', ifc_model, ifc_class='IfcWall')
    instantiating this class as "ios":
      ios.root.create_entity(ifc_model, ifc_class='IfcWall')"""

    module_stack: list[str] = field(default_factory=list)

    def __getattr__(self, module: str) -> Optional[Callable]:
        if module == 'shape' or module.startswith('_'):
            return  # weird PyCharm and/or JupyterLab silent calls
        self.module_stack.append(module)
        return self

    def __call__(self, *args, **kwargs) -> Any:
        try:
            result: Any = ifcopenshell.api.run('.'.join(self.module_stack), *args, **kwargs)
        except Exception as err:
            raise err
        finally:
            self.reset()
        return result

    def reset(self) -> None:
        self.module_stack = []
