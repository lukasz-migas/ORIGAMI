"""Operating-system-specific utilities.

Taken and modified from spyder.utils.system
"""
# Standard library imports
import os


def running_under_pytest():
    """Return True if currently running under py.test.

    This function is used to do some adjustment for testing. The environment
    variable ORIGAMI_PYTEST is defined in conftest.py.
    """
    return bool(os.environ.get("ORIGAMI_PYTEST"))


def get_project_path():
    """Return project path"""

    from pathlib import Path

    return str(Path(__file__).parent.parent)


def get_system_info():
    """Get information about the system"""

    import sys
    import platform

    from origami import __version__

    info = "--- System information ---\n"
    info += f"\nORIGAMI version: {__version__}"
    info += f"\nPlatform: {platform.platform()}"
    info += f"\nPython version: {sys.version}"
    return info


def windows_memory_usage():
    """Return physical memory usage (float)
    Works on Windows platforms only"""

    from ctypes import Structure
    from ctypes import byref
    from ctypes import sizeof
    from ctypes import windll
    from ctypes import c_uint64
    from ctypes.wintypes import DWORD

    class MemoryStatus(Structure):
        """Memory status"""

        _fields_ = [
            ("dwLength", DWORD),
            ("dwMemoryLoad", DWORD),
            ("ullTotalPhys", c_uint64),
            ("ullAvailPhys", c_uint64),
            ("ullTotalPageFile", c_uint64),
            ("ullAvailPageFile", c_uint64),
            ("ullTotalVirtual", c_uint64),
            ("ullAvailVirtual", c_uint64),
            ("ullAvailExtendedVirtual", c_uint64),
        ]

    memorystatus = MemoryStatus()
    # MSDN documetation states that dwLength must be set to MemoryStatus
    # size before calling GlobalMemoryStatusEx
    # https://msdn.microsoft.com/en-us/library/aa366770(v=vs.85)
    memorystatus.dwLength = sizeof(memorystatus)
    windll.kernel32.GlobalMemoryStatusEx(byref(memorystatus))  # noqa
    return float(memorystatus.dwMemoryLoad)


def psutil_phymem_usage():  # noqa
    """
    Return physical memory usage (float)
    Requires the cross-platform psutil (>=v0.3) library
    (https://github.com/giampaolo/psutil)
    """

    import psutil

    # This is needed to avoid a deprecation warning error with
    # newer psutil versions
    try:
        percent = psutil.virtual_memory().percent
    except:
        percent = psutil.phymem_usage().percent  # noqa
    return percent


def import_check(module):
    """Check imports"""

    import importlib.util

    module_loader = importlib.util.find_spec(module)
    found = module_loader is not None
    return found


if import_check("psutil"):
    #  Function `psutil.phymem_usage` was introduced in psutil v0.3.0
    memory_usage = psutil_phymem_usage
elif os.name == "nt":
    # Backup plan for Windows platforms
    memory_usage = windows_memory_usage
else:
    raise ImportError("Feature requires psutil 0.3+ on non Windows platforms")


RUNNING_UNDER_PYTEST = running_under_pytest()
