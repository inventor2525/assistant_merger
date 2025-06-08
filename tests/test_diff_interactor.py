import unittest
from shared_setup import *
from assistant_merger.git_tools import *

class TestDiffInteractor(SharedGitTestCase):
    def test_find_git_repo(self):
        """Test that find_git_repo returns the correct repo root for all files."""
        for filename, repo_file_path in self.file_paths.items():
            with self.subTest(filename=filename):
                repo_root = find_git_repo(repo_file_path)
                self.assertIsNotNone(repo_root, f"Failed to find repo for {filename}")
                self.assertEqual(
                    repo_root,
                    self.repo_path,
                    f"Expected repo root {self.repo_path} for {filename}, got {repo_root}"
                )

    def test_get_git_diff(self):
        """Test that get_git_diff produces the expected diff for each file."""
        for expected_diff_file in self.expected_diffs_dir.glob("*.txt"):
            filename = expected_diff_file.stem + ".py"
            with self.subTest(filename=filename):
                if filename not in self.file_paths:
                    self.skipTest(f"No repo file for {filename}")
                repo_file_path = self.file_paths[filename]

                # Get actual diff
                diff, error = get_git_diff(repo_file_path)
                self.assertIsNone(error, f"Error getting diff for {filename}: {error}")

                # Read expected diff
                with expected_diff_file.open("r", encoding="utf-8") as f:
                    expected_diff = f.read().strip()

                # Compare
                self.assertEqual(
                    diff.strip(),
                    expected_diff,
                    f"Diff mismatch for {filename}"
                )

    def test_add_change_numbers(self):
        """Test that add_change_numbers produces the expected altered diff."""
        for expected_altered_diff_file in self.expected_altered_diffs_dir.glob("*.txt"):
            filename = expected_altered_diff_file.stem + ".py"
            with self.subTest(filename=filename):
                if filename not in self.file_paths:
                    self.skipTest(f"No repo file for {filename}")
                repo_file_path = self.file_paths[filename]

                # Get actual diff
                diff, error = get_git_diff(repo_file_path)
                self.assertIsNone(error, f"Error getting diff for {filename}: {error}")

                # Apply add_change_numbers
                modified_diff, hunks = add_change_numbers(diff, repo_file_path)

                # Read expected altered diff
                with expected_altered_diff_file.open("r", encoding="utf-8") as f:
                    expected_altered_diff = f.read().strip()

                # Compare
                self.assertEqual(
                    modified_diff.strip(),
                    expected_altered_diff,
                    f"Altered diff mismatch for {filename}"
                )

                # Verify hunks
                self.assertGreater(len(hunks), 0, f"No hunks found for {filename}")
                for hunk in hunks:
                    self.assertIn("number", hunk, f"Hunk missing number: {hunk}")
                    self.assertIn("header", hunk, f"Hunk missing header: {hunk}")
                    self.assertIn("content", hunk, f"Hunk missing content: {hunk}")

if __name__ == "__main__":
    unittest.main()