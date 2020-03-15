"""Setup support functions"""
# Standard library imports
from typing import List
from typing import Tuple

# Local imports
import versioneer


def get_version() -> str:
    """The version of ORIGAMI currently checked out

    Returns:
        version : str
    """
    return versioneer.get_version()


def get_requirements_and_links(path: str) -> Tuple[List, List]:
    """Returns list of requirements and links"""
    requirements = get_file_contents(path)
    links, install = [], []
    for requirement in requirements:
        if requirement.startswith("git+") or requirement.startswith("svn+") or requirement.startswith("hg+"):
            links.append(requirement)
        else:
            if requirement.startswith("#"):
                continue
            elif requirement.startswith("-e"):
                install.append(requirement)
            elif requirement.startswith("-r"):
                _install, _links = get_requirements_and_links(requirement.split("-r ")[1])
                links.extend(_links)
                install.extend(_install)
            elif requirement:
                install.append(requirement)
    return install, links


def get_file_contents(path: str):
    """Get contents of a file"""
    with open(path) as f:
        _install = f.read().splitlines()
    return _install
