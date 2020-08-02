""" Provide a version for the ORIGAMI library.

This module uses `versioneer`_ to manage version strings. During development,
`versioneer`_ will compute a version string from the current git revision.
For packaged releases based off tags, the version string is hard coded in the
files packaged for distribution.

Attributes:
    __version__:
        The full version string for this installed ORIGAMI library

Functions:
    base_version:
        Return the base version string, without any "dev", "rc" or local build
        information appended.

.. _versioneer: https://github.com/warner/python-versioneer

"""
# Standard library imports
import json
from distutils.version import LooseVersion

# Third-party imports
import certifi
import urllib3

# Local imports
from origami._version import get_versions

__all__ = ("base_version", "get_latest_version", "compare_versions", "__version__")


def get_latest_version(user_repo: str = "lukasz-migas/ORIGAMI", username: str = "lukasz-migas"):
    """Get latest release of ORIGAMI from GitHub

    Parameters
    ----------
    user_repo : str
        name of the user/repository to be queried
    username : str
        name of the user to make the required header

    Returns
    -------
    latest_version : str
        latest version that is recorded by the tag
    url : str
        url to the latest version
    failed : bool
        indicates whether the request was successful - if version could not be retrieved, `False` will be returned
    """

    # create safe pool
    http = urllib3.PoolManager(cert_reqs="CERT_REQUIRED", ca_certs=certifi.where())

    # get latest release
    response = http.request(
        "GET",
        f"https://api.github.com/repos/{user_repo}/releases/latest",
        headers=urllib3.make_headers(user_agent=username),
    )

    latest_version = "0.0.0.0"
    url = None
    failed = True
    if response.status == 200:
        data = response.data.decode()
        data = json.loads(data)
        latest_version = data["tag_name"]
        url = data["html_url"]
        failed = False
    del http

    return latest_version, url, failed


def compare_versions(new_version: str, old_version: str) -> bool:
    """Compare current and latest version of the software"""
    return LooseVersion(new_version) > LooseVersion(old_version)


def base_version() -> str:
    """Return base version of the package"""
    return _base_version_helper(__version__)


def _base_version_helper(version: str) -> str:
    import re

    version_pat = re.compile(r"^(\d+\.\d+\.\d+)((?:dev|rc).*)?")
    match = version_pat.search(version)
    assert match is not None
    return match.group(1)


__version__ = get_versions()["version"]
del get_versions
