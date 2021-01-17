"""Setup support functions"""
# Standard library imports
from typing import List
from typing import Tuple
import os
import codecs
import re

META_PATH = os.path.join("src", "imimspy", "__init__.py")
HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """
    Build an absolute path from *parts* and return the contents of the
    resulting file.  Assume UTF-8 encoding.
    """
    with codecs.open(os.path.join(HERE, *parts), "rb", "utf-8") as f:
        return f.read()


META_FILE = read(META_PATH)


def find_meta(meta):
    """
    Extract __*meta*__ from META_FILE.
    """
    meta_match = re.search(r"^__{meta}__ = ['\"]([^'\"]*)['\"]".format(meta=meta), META_FILE, re.M)
    if meta_match:
        return meta_match.group(1)
    raise RuntimeError("Unable to find __{meta}__ string.".format(meta=meta))


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
