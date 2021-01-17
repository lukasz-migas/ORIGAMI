"""Init"""
# Standard library imports
import os

PWD = os.path.dirname(os.path.realpath(__file__))
CWD = os.getcwd()
if PWD != CWD:
    os.chdir(PWD)

__version__ = "2.0.0.dev"
__title__ = "ORIGAMI"
__description__ = "ORIGAMI: ion mobility mass spectrometry analysis software"
__project_url__ = "https://github.com/lukasz-migas/origami"
__issue_url__ = __project_url__ + "/issues"
__url__ = "https://github.com/lukasz-migas/origami"
__uri__ = __url__
__website_url__ = "https://origami.lukasz-migas.com"
__doc__ = __description__ + " <" + __uri__ + ">"
__author__ = "Lukasz G. Migas"
__email__ = "lukas.migas@yahoo.com"
__licence__ = "Apache license 2.0"
__copyright__ = "Copyright (c) 2017-present Lukasz G. Migas"
