import unittest
import tempfile
import shutil
import subprocess
from pathlib import Path
from assistant_merger.git_tools import get_git_diff, add_change_numbers, apply_changes

class TestDiffInteractor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo_path = self.temp_dir / "repo"
        self.repo_path.mkdir()
        
        subprocess.run(["git", "init"], cwd=self.repo_path, check=True)
        
        self.test_file = self.repo_path / "vector2.py"
        v1_path = Path(__file__).parent / "examples/vector2_v1.py"
        shutil.copy(v1_path, self.test_file)
        
        subprocess.run(["git", "add", "vector2.py"], cwd=self.repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.repo_path, check=True)
        
        v2_path = Path(__file__).parent / "examples/vector2_v2.py"
        shutil.copy(v2_path, self.test_file)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_git_diff(self):
        diff, error = get_git_diff(self.test_file)
        self.assertIsNone(error)
        expected_path = Path(__file__).parent / "examples/expected_diff_v1_v2.txt"
        with expected_path.open("r", encoding="utf-8") as f:
            expected_diff = f.read()
        self.assertEqual(diff.strip(), expected_diff.strip())

    def test_change_numbering(self):
        diff, error = get_git_diff(self.test_file)
        modified_diff, hunks = add_change_numbers(diff)
        self.assertRegex(modified_diff, r"\(Change #1\)")
        self.assertRegex(modified_diff, r"\(Change #2\)")
        self.assertRegex(modified_diff, r"\(Change #3\)")
        self.assertEqual(len(hunks), 3)
        self.assertIn("import math", hunks[0]["content"])
        self.assertIn("# Optimized addition", hunks[1]["content"])
        self.assertIn("subtract", hunks[2]["content"])

    def test_apply_accept_both(self):
        diff, error = get_git_diff(self.test_file)
        modified_diff, hunks = add_change_numbers(diff)
        actions = [
            {"action": "accept", "change_id": "change_1", "content": ""},
            {"action": "accept", "change_id": "change_2", "content": ""},
            {"action": "accept", "change_id": "change_3", "content": ""}
        ]
        model_response = "\n".join([f"{a['action']} {a['change_id']}" for a in actions])
        apply_changes(self.test_file, diff, model_response)
        
        with self.test_file.open("r", encoding="utf-8") as f:
            content = f.read()
        expected_path = Path(__file__).parent / "examples/expected_test_apply_accept_both_result.txt"
        with expected_path.open("r", encoding="utf-8") as f:
            expected_content = f.read()
        self.assertEqual(content.strip(), expected_content.strip())

    def test_apply_accept_reject(self):
        diff, error = get_git_diff(self.test_file)
        modified_diff, hunks = add_change_numbers(diff)
        actions = [
            {"action": "accept", "change_id": "change_1", "content": ""},
            {"action": "accept", "change_id": "change_2", "content": ""},
            {"action": "reject", "change_id": "change_3", "content": ""}
        ]
        model_response = "\n".join([f"{a['action']} {a['change_id']}" for a in actions])
        apply_changes(self.test_file, diff, model_response)
        
        with self.test_file.open("r", encoding="utf-8") as f:
            content = f.read()
        expected_path = Path(__file__).parent / "examples/expected_test_apply_accept_reject_result.txt"
        with expected_path.open("r", encoding="utf-8") as f:
            expected_content = f.read()
        self.assertEqual(content.strip(), expected_content.strip())

    def test_apply_reject_accept(self):
        diff, error = get_git_diff(self.test_file)
        modified_diff, hunks = add_change_numbers(diff)
        actions = [
            {"action": "reject", "change_id": "change_1", "content": ""},
            {"action": "reject", "change_id": "change_2", "content": ""},
            {"action": "accept", "change_id": "change_3", "content": ""}
        ]
        model_response = "\n".join([f"{a['action']} {a['change_id']}" for a in actions])
        apply_changes(self.test_file, diff, model_response)
        
        with self.test_file.open("r", encoding="utf-8") as f:
            content = f.read()
        expected_path = Path(__file__).parent / "examples/expected_test_apply_reject_accept_result.txt"
        with expected_path.open("r", encoding="utf-8") as f:
            expected_content = f.read()
        self.assertEqual(content.strip(), expected_content.strip())

    def test_apply_accept_merge(self):
        diff, error = get_git_diff(self.test_file)
        modified_diff, hunks = add_change_numbers(diff)
        merge_content = "    def multiply(self, other):\n        return Vector2(self.x * other.x, self.y * other.y)\n"
        actions = [
            {"action": "accept", "change_id": "change_1", "content": ""},
            {"action": "accept", "change_id": "change_2", "content": ""},
            {"action": "merge", "change_id": "change_3", "content": merge_content}
        ]
        model_response = "\n".join([f"{a['action']} {a['change_id']} {a['content']}" if a['action'] == "merge" else f"{a['action']} {a['change_id']}" for a in actions])
        apply_changes(self.test_file, diff, model_response)
        
        with self.test_file.open("r", encoding="utf-8") as f:
            content = f.read()
        expected_path = Path(__file__).parent / "examples/expected_test_apply_accept_merge_result.txt"
        with expected_path.open("r", encoding="utf-8") as f:
            expected_content = f.read()
        self.assertEqual(content.strip(), expected_content.strip())

if __name__ == "__main__":
    unittest.main()