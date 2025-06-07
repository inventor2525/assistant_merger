from pathlib import Path
from typing import List
from .git_tools import get_git_diff, apply_changes

def run_diff_interactor(file_paths: List[str]) -> None:
    """Run the interactive diff interactor for a list of file paths."""
    for file_path_str in file_paths:
        file_path = Path(file_path_str).resolve()
        print(f"\nProcessing file: {file_path}")

        while True:
            # Get git diff
            diff, error = get_git_diff(file_path)
            if error:
                print(f"Error: {error}")
                break
            if not diff:
                print("No changes to process.")
                break

            # Display diff
            print("\n=== Diff Output ===")
            print(diff)
            print("\n=== End Diff ===")

            # Get model response
            print("\nEnter model response (format: accept change_1, reject change_2, merge change_3 <content>):")
            print("Or type 'exit' to move to next file.")
            response = ""
            while True:
                line = input()
                if line.strip().lower() == "exit":
                    break
                response += line + "\n"
                if not line.strip():
                    break

            if response.strip().lower() == "exit":
                break

            # Apply changes
            if apply_changes(file_path, diff, response):
                print("Changes applied. Running diff again...")
            else:
                print("Failed to apply changes.")
                break

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m assistant_merger.console_app <file_path> [<file_path> ...]")
        sys.exit(1)
    run_diff_interactor(sys.argv[1:])