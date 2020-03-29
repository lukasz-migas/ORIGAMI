# Standard library imports
import os
import sys
import traceback
# from distutils.errors import CCompilerError
# from distutils.errors import DistutilsExecError
from distutils.errors import DistutilsPlatformError
# Extension must be loaded AFTER setup
from distutils.command.build_ext import build_ext

# Third-party imports
# from setuptools import Extension
from setuptools import setup
from setuptools import find_packages

# Local imports
from _setup_utils import get_version
from _setup_utils import get_requirements_and_links


def has_option(name):
    try:
        sys.argv.remove("--%s" % name)
        return True
    except ValueError:
        pass
    # allow passing all cmd line options also as environment variables
    env_val = os.getenv(name.upper().replace("-", "_"), "false").lower()
    if env_val == "true":
        return True
    return False


include_diagnostics = has_option("include-diagnostics")
force_cythonize = has_option("force-cythonize")


def make_extensions():
    is_ci = bool(os.getenv("CI", ""))
    try:
        import numpy
    except ImportError:
        print("Installation requires `numpy`")
        raise

    macros = []
    try:
        from Cython.Build import cythonize

        cython_directives = {"embedsignature": True, "profile": include_diagnostics}
        if include_diagnostics:
            macros.append(("CYTHON_TRACE_NOGIL", "1"))
        if is_ci and include_diagnostics:
            cython_directives["linetrace"] = True

        extensions = cythonize([], compiler_directives=cython_directives, force=force_cythonize)
    except ImportError:
        extensions = []
    return extensions


class BuildFailed(Exception):
    def __init__(self):
        self.cause = sys.exc_info()[1]  # work around py 2/3 different syntax

    def __str__(self):
        return str(self.cause)


class ve_build_ext(build_ext):
    # This class allows C extension building to fail.

    def run(self):
        try:
            build_ext.run(self)
        except DistutilsPlatformError:
            traceback.print_exc()
            raise BuildFailed()

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except ext_errors:
            traceback.print_exc()
            raise BuildFailed()
        except ValueError:
            # this can happen on Windows 64 bit, see Python issue 7511
            traceback.print_exc()
            if "'path'" in str(sys.exc_info()[1]):  # works with both py 2/3
                raise BuildFailed()
            raise


CMD_CLASS = {"build_ext": ve_build_ext}


def status_msgs(*msgs):
    print("*" * 75)
    for msg in msgs:
        print(msg)
    print("*" * 75)


VERSION = get_version()
DESCRIPTION = "ORIGAMI: ion mobility mass spectrometry analysis software"

with open("README.md") as f:
    LONG_DESCRIPTION = f.read()

PACKAGE_NAME = "origami"
MAINTAINER = "Lukasz G. Migas"
MAINTAINER_EMAIL = "lukas.migas@yahoo.com"
URL = "https://github.com/lukasz-migas/origami"
LICENSE = "Apache license 2.0"
DOWNLOAD_URL = "https://github.com/lukasz-migas/origami"
INSTALL_REQUIRES, DEPENDENCY_LINKS = get_requirements_and_links("requirements/requirements-std.txt")
PACKAGES = [package for package in find_packages()]
PACKAGE_DATA = {"": []}

print(INSTALL_REQUIRES)

CLASSIFIERS = [
    "Intended Audience :: Science/Research",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Operating System :: Microsoft :: Windows",
    "Natural Language :: English",
]


def run_setup(include_c_ext=True):
    setup(
        name=PACKAGE_NAME,
        author=MAINTAINER,
        author_email=MAINTAINER_EMAIL,
        maintainer=MAINTAINER,
        maintainer_email=MAINTAINER_EMAIL,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        long_description_content_type="text/markdown",
        license=LICENSE,
        url=URL,
        version=VERSION,
        download_url=DOWNLOAD_URL,
        install_requires=INSTALL_REQUIRES,
        dependency_links=DEPENDENCY_LINKS,
        packages=PACKAGES,
        classifiers=CLASSIFIERS,
        package_dir={"origami": "origami"},
        package_data=PACKAGE_DATA,
        entry_points={"console_scripts": ["origami = origami.__main__:main"]},
        cmdclass=CMD_CLASS,
        ext_modules=make_extensions() if include_c_ext else None,
        include_package_data=True,
    )


if __name__ == "__main__":

    try:
        run_setup(include_c_ext=True)
    except Exception as exc:
        print(exc)
        run_setup(include_c_ext=False)

        status_msgs(
            "WARNING: The C extension could not be compiled, speedups are not enabled." "Plain-Python build succeeded."
        )
