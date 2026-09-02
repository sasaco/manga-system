import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "repo_check", ROOT / "scripts" / "repo_check.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class RepositoryCheckTests(unittest.TestCase):
    def test_repository_infrastructure_is_coherent(self):
        self.assertEqual(MODULE.check_repo(ROOT), [])


if __name__ == "__main__":
    unittest.main()
