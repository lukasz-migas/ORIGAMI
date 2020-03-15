"""Init"""
# Standard library imports
import os

# Local imports
from origami._version import get_versions

__version__ = get_versions()["version"]
PWD = os.path.dirname(os.path.realpath(__file__))
CWD = os.getcwd()
if PWD != CWD:
    os.chdir(PWD)

__project_url__ = "https://github.com/lukasz-migas/origami"
__issue_url__ = __project_url__ + "/issues"
__trouble_url__ = "https://github.com/lukasz-migas/origami"
__trouble_url_short__ = "https://github.com/lukasz-migas/origami"
__website_url__ = "https://origami.lukasz-migas.com"

__all__ = ["__version__"]
