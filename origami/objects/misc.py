"""Misc containers"""
# Standard library imports
from typing import Dict
from collections import namedtuple

FileItem = namedtuple("FileItem", ["variable", "path", "scan_range", "mz_range", "im_on", "information"])


class User:
    """User"""

    def __init__(self, full_name: str, email: str, institution: str):
        self.full_name = full_name
        self.email = email
        self.institution = institution

    def __repr__(self) -> str:
        """Return repr"""
        return f"{self.__class__.__name__}<{self.full_name}; {self.email}; {self.institution}>"

    @property
    def user_details(self) -> str:
        """Returns pretty formatted user details"""
        _user = self.full_name
        email = self.email
        _user += f" :: {email if email else 'N/A'}"
        institution = self.institution
        _user += f" :: {institution if institution else 'N/A'}"
        return _user

    def to_dict(self) -> Dict[str, str]:
        """Returns dictionary of values"""
        return {"full_name": self.full_name, "email": self.email, "institution": self.institution}


class CompareItem:
    """Spectrum comparison object"""

    __slots__ = ["document", "title", "legend"]

    def __init__(self, document: str = None, title: str = None, legend: str = None):
        self.document = document
        self.title = title
        self.legend = legend
