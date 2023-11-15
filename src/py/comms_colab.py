import IPython
import ipywidgets as widgets
from ipykernel import comm
from google.colab import output
import ifcopenshell


def send_ifc_stream(ifc_model: ifcopenshell.file) -> comm.comm.Comm:
    return comm.Comm(
        target_name='xeokitViz', data={'ifcStr': ifc_model.to_string()}
    )


def update_viz(ifc_model: ifcopenshell.file) -> widgets.Button:
    button = widgets.Button(description="REFRESH VIEW")

    def _send_ifc_stream(button: widgets.Button) -> comm.comm.Comm:
        return send_ifc_stream(ifc_model)

    button.on_click(_send_ifc_stream)
    return button


def _request_ifc():
    success = True if send_ifc_stream(globals()['_ifc_model']) else False
    return IPython.display.JSON({'success': success})


output.register_callback('notebook._request_ifc', _request_ifc)
