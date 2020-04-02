# Third-party imports
import pytest

# Local imports
from origami.document import document as Document
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
