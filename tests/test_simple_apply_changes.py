import unittest
from shared_setup import *
from assistant_merger.git_tools import *

class TestApplyChanges(SharedGitTestCase):
	def test_apply_all_yes(self):
		"""Test applying 'Yes' to all changes results in v2 file content."""
		for v1_file in self.v1_dir.glob("*.py"):
			filename = v1_file.name
			with self.subTest(filename=filename):
				repo_file_path = self.file_paths.get(filename)
				if not repo_file_path:
					self.skipTest(f"No repo file for {filename}")

				# Get diff and hunks
				diff, error = get_git_diff(repo_file_path)
				self.assertIsNone(error, f"Error getting diff for {filename}: {error}")
				_, hunks = add_change_numbers(diff, repo_file_path)
				self.assertGreater(len(hunks), 0, f"No hunks found for {filename}")

				# Generate LLM response with 'Yes' for all changes
				llm_response = "\n".join(f"Change #{i+1}, Yes" for i in range(len(hunks)))

				# Apply changes
				merged_content = apply_changes(repo_file_path, diff, llm_response)

				# Read expected v2 content
				v2_file = self.v2_dir / filename
				with v2_file.open("r", encoding="utf-8") as f:
					expected_content = f.read()

				# Compare
				self.assertEqual(
					merged_content,
					expected_content,
					f"Merged content for {filename} (all Yes) does not match v2"
				)

	def test_apply_all_no(self):
		"""Test applying 'No' to all changes results in v1 file content."""
		for v1_file in self.v1_dir.glob("*.py"):
			filename = v1_file.name
			with self.subTest(filename=filename):
				repo_file_path = self.file_paths.get(filename)
				if not repo_file_path:
					self.skipTest(f"No repo file for {filename}")

				# Get diff and hunks
				diff, error = get_git_diff(repo_file_path)
				self.assertIsNone(error, f"Error getting diff for {filename}: {error}")
				_, hunks = add_change_numbers(diff, repo_file_path)
				self.assertGreater(len(hunks), 0, f"No hunks found for {filename}")

				# Generate LLM response with 'No' for all changes
				llm_response = "\n".join(f"Change #{i+1}, No" for i in range(len(hunks)))

				# Apply changes
				merged_content = apply_changes(repo_file_path, diff, llm_response)

				# Read expected v1 content
				with v1_file.open("r", encoding="utf-8") as f:
					expected_content = f.read()

				# Compare
				self.assertEqual(
					merged_content,
					expected_content,
					f"Merged content for {filename} (all No) does not match v1"
				)

if __name__ == "__main__":
	unittest.main()