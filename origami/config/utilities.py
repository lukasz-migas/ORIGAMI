"""Various utility fuctions"""


def clean_document(document):
    """Clean document"""
    document.title = parse_document_title(document.title)
    return document


def parse_document_title(document_title):
    """Parse document title"""
    if document_title is None:
        return document_title
    if document_title.endswith(".origami"):
        document_title = document_title.split(".origami")[0]
    return document_title
