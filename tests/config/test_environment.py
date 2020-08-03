# Third-party imports
import pytest

# Local imports
from origami.objects.document import DocumentStore
from origami.config.environment import DOCUMENT_TYPE_ATTRIBUTES
from origami.config.environment import Environment


class TestEnvironment:
    @staticmethod
    def test_init():
        env = Environment()
        assert len(env) == 0
        assert env.n_documents == len(env)

    def test_add(self, tmpdir_factory):
        path = str(tmpdir_factory.mktemp("TEST.origami"))
        document = DocumentStore(path)
        document.title = "TEST"
        env = Environment()
        env.add(document)
        assert env.n_documents == 1

        doc = env.on_get_document("TEST")
        assert doc == document

    def test_remove(self, tmpdir_factory):
        path = str(tmpdir_factory.mktemp("TEST.origami"))
        document = DocumentStore(path)
        document.title = "TEST"
        env = Environment()
        env.add(document)
        assert env.n_documents == 1
        assert env.current == "TEST"

        with pytest.raises(KeyError):
            env.remove("TEST_NOT_THERE")
        env.remove("TEST")
        assert env.n_documents == 0
        assert env.current != "TEST"

    def test_open(self, get_origami_document):
        path = get_origami_document
        env = Environment()
        env.open(path)
        assert env.n_documents == 1
        assert env.current == "DOCUMENT"
        titles = env.titles
        assert "DOCUMENT" in titles

    def test_load(self, get_origami_document):
        path = get_origami_document
        env = Environment()
        env.load(path)
        assert env.n_documents == 1

    def test_duplicate(self, get_origami_document, tmpdir_factory):
        path = get_origami_document
        env = Environment()
        env.open(path)
        assert env.n_documents == 1
        assert env.current == "DOCUMENT"

        # with overwrite
        path2 = str(tmpdir_factory.mktemp("another-document-path", False))
        document = env.duplicate("DOCUMENT", path2, True)
        assert isinstance(document, DocumentStore)
        assert env.n_documents == 2

        doc_list = env.get_document_list()
        assert len(doc_list) == 2

        # without overwrite
        path3 = str(tmpdir_factory.mktemp("another-document-path-2w31.origami", False))
        document = env.duplicate("DOCUMENT", path3)
        assert isinstance(document, DocumentStore) is False
        assert env.n_documents == 2

    def test_dict_funcs(self, get_origami_document):
        path = get_origami_document
        env = Environment()
        env.load(path)
        assert env.n_documents == 1

        for title in env.keys():
            assert isinstance(title, str)

        for document in env.values():
            assert isinstance(document, DocumentStore)

        for title, document in env.items():
            assert isinstance(title, str)
            assert isinstance(document, DocumentStore)

        document = env.pop("DOCUMENT")
        assert env.n_documents == 0
        assert env.current != "DOCUMENT"

        env.add(document)
        assert env.n_documents == 1
        assert env.current == "DOCUMENT"
        env.clear()
        assert env.n_documents == 0
        assert env.current != "DOCUMENT"

    def test_set_get(self, get_origami_document, tmpdir_factory):
        path = get_origami_document
        env = Environment()
        env.open(path)

        # check contains
        assert "DOCUMENT" in env

        # check get item
        document = env["DOCUMENT"]
        assert isinstance(document, DocumentStore)
        assert document.path == path
        assert document.title == "DOCUMENT"

        # rename
        assert env.current == "DOCUMENT"
        env.rename("DOCUMENT", "DOC")
        assert "DOC" in env
        assert env.current == "DOC"

        # check get item
        document = env.get("DOC")
        assert isinstance(document, DocumentStore)
        assert document.path == path
        assert document.title == "DOC"

        # create another document
        path = str(tmpdir_factory.mktemp("TEST.origami"))
        document = DocumentStore(path)
        env.add(document)
        assert env.current == "TEST"
        assert "TEST" in env

    def test_new(self, tmp_path):
        env = Environment()
        for document_type, document_attributes in DOCUMENT_TYPE_ATTRIBUTES.items():
            document = env.new(document_type, str(tmp_path))
            assert ".origami" in document.path
            assert document.data_type == document_attributes["data_type"]
            assert document.file_format == document_attributes["file_format"]

        doc_list = env.get_document_list()
        assert len(doc_list) == env.n_documents
