"""ORIGAMI

You can start ORIGAMI from the command line by simply typing `origami` or you can start few of the available
widgets by invoking `origami --widget WIDGET_NAME`
"""
# Standard library imports
import os
import sys
import argparse

# Local imports
from origami.utils.version import __version__

__author__ = "Lukasz G. Migas (l.g.migas@tudelft.nl)"

PWD_PATH = os.path.dirname(__file__)
os.chdir(PWD_PATH)
sys.path.append(PWD_PATH)

ALLOWED_WIDGETS = ("ccs", "unidec")


def run_origami():
    """Execute main function"""
    from origami.main import ORIGAMI

    app = ORIGAMI()
    app.start()


def run_ccs():
    """Run CCS calibration panel"""
    from origami.main import App

    app = App()

    from origami.widgets.ccs.panel_ccs_calibration import PanelCCSCalibration

    dlg = PanelCCSCalibration(None)
    dlg.Show()
    app.MainLoop()


def run_unidec():
    """Run UniDec deconvolution panel"""
    from origami.main import App

    app = App()

    from origami.widgets.unidec.panel_process_unidec import PanelProcessUniDec

    dlg = PanelProcessUniDec(None, None)
    dlg.Show()
    app.MainLoop()


def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument(
        "-v", "--version", action="version", version=__version__, help="Show program's  version number and exit"
    )
    parser.add_argument("--author", action="version", version=__author__, help="Show program's author name and exit")
    parser.add_argument("--widget", help="Specify which widget should be run.", choices=ALLOWED_WIDGETS)

    args = parser.parse_args()
    if args.widget == "ccs":
        run_ccs()
    elif args.widget == "unidec":
        run_unidec()
    else:
        run_origami()


if __name__ == "__main__":
    sys.exit(main())
