from IPython.core.magic import register_cell_magic
from IPython.display import HTML
import ifcopenshell


@register_cell_magic
def create_xeokit_script(line, src):
    saved = False
    with open('/usr/local/share/jupyter/nbextensions/xeokit-viz.js', 'w') as f:
        f.write(src)
        saved = True
    return 'xeokit-viz.js was saved' if saved else 'an error occurred'


@register_cell_magic
def create_xeokit_style(line, src):
    saved = False
    with open('/usr/local/share/jupyter/nbextensions/xeokit-style.css', 'w') as f:
        f.write(src)
        saved = True
    return 'xeokit-style.css was saved' if saved else 'an error occurred'


def _show_ifc(
        ifc_model: ifcopenshell.entity_instance, ipython_button: bool = False
) -> HTML:
    toolbar_classes = "bimToolbar"
    tree_classes = ""
    if ipython_button:
        toolbar_classes += " toolbarWithIpythonButton"
        tree_classes += "treeWithIpythonButton"
        display(update_viz(ifc_model))
    return HTML("index.html")
