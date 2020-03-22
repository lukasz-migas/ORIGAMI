"""ORIGAMI main entry point"""
# Standard library imports
import os
import sys
import argparse

# Local imports
from origami.main import ORIGAMI
from origami.utils.version import __version__

__author__ = "Lukasz G. Migas"

PWD_PATH = os.path.dirname(__file__)
os.chdir(PWD_PATH)
sys.path.append(PWD_PATH)


def main():
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument(
        "-v", "--version", action="version", version=__version__, help="Show program's  version number and exit"
    )
    parser.add_argument("--author", action="version", version=__author__, help="Show program's author name and exit")

    args = parser.parse_args()

    app = ORIGAMI(redirect=False)
    app.start()


if __name__ == "__main__":
    sys.exit(main())
