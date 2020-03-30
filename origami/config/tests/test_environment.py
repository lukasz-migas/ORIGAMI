# Local imports
from origami.config.environment import Environment


class TestEnvironment:
    @staticmethod
    def test_init():
        env = Environment()
        assert len(env) == 0
        assert env.n_documents == len(env)
