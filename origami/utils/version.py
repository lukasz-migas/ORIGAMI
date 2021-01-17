""" Provide a version for the ORIGAMI library."""
# Standard library imports
import json
from distutils.version import LooseVersion

# Third-party imports
import certifi
import urllib3

__all__ = (
    "get_latest_version",
    "compare_versions",
)


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
