# Third-party imports
import pytest

# Local imports
from origami.document import document as Document
from origami.config.environment import DOCUMENT_TYPE_ATTRIBUTES
from origami.config.environment import Environment


class TestEnvironment:
    @staticmethod
    def test_init():
        env = Environment()
        assert len(env) == 0
        assert env.n_documents == len(env)

    def test_add(self):
        document = Document()
        document.title = "TEST"
        env = Environment()
        env.add(document)
        assert env.n_documents == 1

    def test_remove(self):
        document = Document()
        document.title = "TEST"
        env = Environment()
        env.add(document)
        with pytest.raises(KeyError):
            env.remove("TEST_NOT_THERE")

        env.remove("TEST")

    def test_new(self, tmp_path):
        env = Environment()
        for document_type, document_attributes in DOCUMENT_TYPE_ATTRIBUTES.items():
            document = env.new(document_type, str(tmp_path))
            assert ".origami" in document.path
            assert document.data_type == document_attributes["data_type"]
            assert document.file_format == document_attributes["file_format"]
