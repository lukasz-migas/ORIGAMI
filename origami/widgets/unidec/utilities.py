"""UniDec utilities"""
import os
import pathlib


def get_uri():
    """Get path to the unidec html file"""
    path = os.path.dirname(__file__)
    html_file = pathlib.Path(path)
    html_file = html_file.joinpath("index.html")
    return html_file.as_uri()


def about_unidec(parent):
    """About UniDec"""
    from origami.gui_elements.panel_html_viewer import PanelHTMLViewer

    html_link = get_uri()
    dlg = PanelHTMLViewer(parent, link=html_link)
    dlg.CenterOnParent()
    return dlg
