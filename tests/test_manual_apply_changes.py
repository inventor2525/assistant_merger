import unittest
from pathlib import Path
from shared_setup import *
from assistant_merger.git_tools import *

class TestManualApplyChanges(SharedGitTestCase):
    def test_manual_apply_changes(self):
        """Test applying manual change decisions from input files and verify against expected outputs."""
        manual_test_dir = Path(__file__).parent / "examples" / "manual_tests"
        input_dir = manual_test_dir / "input"
        expected_output_dir = manual_test_dir / "expected_output"

        name_pattern = re.compile(r'^(.*)_(\d*)\.txt$')
        # Iterate over .txt files in input directory
        for input_file in input_dir.glob("*.txt"):
            expecteds_filename = input_file.stem + ".py"  # Expect corresponding .py file
            filename = name_pattern.match(input_file.name).group(1) + ".py"
            with self.subTest(filename=expecteds_filename):
                # Check if expected output exists
                expected_output_file = expected_output_dir / expecteds_filename
                if not expected_output_file.exists():
                    self.skipTest(f"No expected output file for {expecteds_filename}")

                # Load input file (LLM response)
                with input_file.open("r", encoding="utf-8") as f:
                    llm_response = f.read().strip()

                # Get file to test
                repo_file_path = self.file_paths.get(filename)
                if not repo_file_path:
                    self.skipTest(f"No repo file for {filename}")

                # Get diff and hunks
                diff, error = get_git_diff(repo_file_path)
                self.assertIsNone(error, f"Error getting diff for {filename}: {error}")
                _, hunks = add_change_numbers(diff, repo_file_path)
                self.assertGreater(len(hunks), 0, f"No hunks found for {filename}")

                # Apply changes
                merged_content = apply_changes(repo_file_path, diff, llm_response)

                # Load expected output
                with expected_output_file.open("r", encoding="utf-8") as f:
                    expected_content = f.read()

                # Compare
                self.assertEqual(
                    merged_content,
                    expected_content,
                    f"Merged content for {filename} does not match expected output"
                )

if __name__ == "__main__":
    unittest.main()