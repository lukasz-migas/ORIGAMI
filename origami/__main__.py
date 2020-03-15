"""ORIGAMI main entry point"""
# Standard library imports
import os
import sys

# Local imports
from origami.main import ORIGAMI

__author__ = "Lukasz G. Migas"

PWD_PATH = os.path.dirname(__file__)
os.chdir(PWD_PATH)
sys.path.append(PWD_PATH)


def main():
    app = ORIGAMI(redirect=False)
    app.start()


if __name__ == "__main__":
    main()
