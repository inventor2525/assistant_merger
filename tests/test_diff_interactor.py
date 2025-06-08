import unittest
import tempfile
import shutil
import subprocess
import random
import string
from pathlib import Path
from assistant_merger.git_tools import find_git_repo, get_git_diff, add_change_numbers

class TestDiffInteractor(unittest.TestCase):
    def setUp(self):
        # Create temporary directory for git repository
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo_path = self.temp_dir / "repo"
        self.repo_path.mkdir()

        # Initialize git repository
        subprocess.run(["git", "init"], cwd=self.repo_path, check=True)

        # Get paths to v1 and v2 example files
        self.examples_dir = Path(__file__).parent / "examples"
        self.v1_dir = self.examples_dir / "v1"
        self.v2_dir = self.examples_dir / "v2"
        self.expected_diffs_dir = self.examples_dir / "expected_diffs"
        self.expected_altered_diffs_dir = self.examples_dir / "expected_altered_diffs"

        # Dictionary to track file paths in repo: {filename: repo_path}
        self.file_paths = {}

        # Copy v1 files to randomized paths in repo, add, and commit
        for v1_file in self.v1_dir.glob("*.py"):
            # Generate random path (e.g., subdir1/subdir2/filename)
            subdirs = []
            for _ in range(random.randint(0, 3)):  # 0 to 3 levels of subdirectories
                subdir = ''.join(random.choices(string.ascii_lowercase, k=8))
                subdirs.append(subdir)
            repo_file_dir = self.repo_path / "/".join(subdirs)
            repo_file_dir.mkdir(parents=True, exist_ok=True)
            repo_file_path = repo_file_dir / v1_file.name

            # Copy v1 file
            shutil.copy(v1_file, repo_file_path)
            self.file_paths[v1_file.name] = repo_file_path

            # Add and commit
            subprocess.run(["git", "add", repo_file_path], cwd=self.repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.repo_path, check=True)

        # Replace with v2 files
        for v2_file in self.v2_dir.glob("*.py"):
            if v2_file.name in self.file_paths:
                shutil.copy(v2_file, self.file_paths[v2_file.name])

    def tearDown(self):
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)

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