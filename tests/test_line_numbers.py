import unittest
from shared_setup import SharedGitTestCase
from assistant_merger.git_tools import get_git_diff, add_change_numbers

class TestLineNumbers(SharedGitTestCase):
    def test_line_numbers_vector2(self):
        """Test line numbers in modified diff output for vector2.py."""
        filename = "utils_2.py"
        repo_file_path = self.file_paths.get(filename)
        if not repo_file_path:
            self.skipTest(f"No repo file for {filename}")

        # Get diff and debug
        diff, error = get_git_diff(repo_file_path)
        print(f"\nDebug: Diff for {filename}:\n{diff}")
        print(f"Debug: Error for {filename}: {error}")
        self.assertIsNone(error, f"Error getting diff for {filename}: {error}")

        # Apply add_change_numbers with line numbers
        modified_diff, _ = add_change_numbers(diff, repo_file_path, add_line_numbers=True)

        # Print the modified diff for verification
        print(f"\nModified diff with line numbers for {filename}:\n{modified_diff}")

        # Mark test as incomplete
        self.skipTest("Test incomplete, printed diff for manual verification")

if __name__ == "__main__":
    unittest.main()