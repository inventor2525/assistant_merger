import tempfile
import shutil
import subprocess
import random
import string
from pathlib import Path
import unittest

class SharedGitTestCase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        
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