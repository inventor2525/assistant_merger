import os
import subprocess
import re
from pathlib import Path
from typing import Optional, Tuple, List, Dict

def find_git_repo(file_path: Path) -> Optional[Path]:
    """Find the git repository root for a given file path."""
    current = file_path.parent
    while current != current.parent:
        if (current / ".git").is_dir():
            return current
        current = current.parent
    return None

def get_git_diff(file_path: Path) -> Tuple[str, Optional[str]]:
    """Get the git diff for a specific file."""
    repo_path = find_git_repo(file_path)
    if not repo_path:
        return "", f"No git repository found for {file_path}"
    try:
        relative_path = file_path.relative_to(repo_path)
        result = subprocess.run(
            ["git", "diff", "--unified=0", str(relative_path)],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0 and result.stdout:
            s = result.stdout.split("\n")
            return "\n".join(s[4:]), None
        return "", f"No changes or file not tracked: {relative_path}"
    except subprocess.SubprocessError as e:
        return "", f"Error running git diff: {e}"
    except ValueError as e:
        return "", f"Invalid file path relative to repo: {e}"

def add_change_numbers(diff: str, file_path: Path) -> Tuple[str, List[Dict[str, str]]]:
    """Add change numbers to diff hunks, include post-hunk content, and return modified diff with hunk metadata."""
    if not diff:
        return "", []

    # Read current file content
    try:
        with open(file_path, 'r') as f:
            file_lines = f.read().splitlines()
    except Exception as e:
        return "", [{"error": f"Could not read file: {e}"}]

    lines = diff.splitlines()
    modified_lines = []
    change_count = 0
    hunks = []
    current_hunk_lines = []
    hunk_start = None

    # Regex to match hunk headers like @@ -old,new +new,lines @@ or @@ -old +new,lines @@
    hunk_pattern = re.compile(r'^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,(\d+))? @@(?: .*)?$')

    for line in lines:
        hunk_match = hunk_pattern.match(line)
        if hunk_match:
            if current_hunk_lines and hunk_start:
                hunks.append({
                    "number": f"Change #{change_count}",
                    "header": hunk_start,
                    "content": "\n".join(current_hunk_lines)
                })
                current_hunk_lines = []
            change_count += 1
            # Extract new file start line and number of lines
            new_start = int(hunk_match.group(2))
            new_lines = int(hunk_match.group(3)) if hunk_match.group(3) else 1
            # Reconstruct clean header without trailing text
            hunk_start = f"@@ -{hunk_match.group(1)} +{new_start},{new_lines} @@"
            modified_lines.append(f"{hunk_start} (Change #{change_count})")
        else:
            current_hunk_lines.append(line)
            modified_lines.append(line)

    if current_hunk_lines and hunk_start:
        hunks.append({
            "number": f"Change #{change_count}",
            "header": hunk_start,
            "content": "\n".join(current_hunk_lines)
        })

    # Process hunks in reverse to get post-hunk content
    result_lines = []
    prev_end = len(file_lines)  # Start from end of file
    for hunk in reversed(hunks):
        # Extract new file start and lines from header
        header = hunk["header"]
        hunk_match = hunk_pattern.match(header)
        if not hunk_match:
            continue
        new_start = int(hunk_match.group(2))
        new_lines = int(hunk_match.group(3)) if hunk_match.group(3) else 1
        # Get lines after this hunk up to previous hunk (or end)
        start_idx = new_start - 1 + new_lines  # 0-based index
        post_hunk_lines = file_lines[start_idx:prev_end]
        # Update prev_end for next iteration
        prev_end = new_start - 1
        # Build hunk output
        hunk_output = [
            f"{hunk['header']} ({hunk['number']})",
            hunk['content'],
            "@@ End Hunk @@"
        ] + post_hunk_lines
        # Prepend to result (building in reverse)
        result_lines = hunk_output + result_lines

    return "\n".join(result_lines), hunks

def apply_changes(file_path: Path, diff: str, llm_response: str) -> str:
    """Apply or revert changes based on LLM response and return merged file content."""
    try:
        with open(file_path, 'r') as f:
            file_lines = f.read().splitlines()
    except Exception as e:
        return f"Error: Could not read file: {e}"

    # Parse LLM response
    approvals = {}
    for line in llm_response.strip().splitlines():
        match = re.match(r'Change #(\d+),\s*(Yes|No)', line, re.IGNORECASE)
        if match:
            change_num = int(match.group(1))
            decision = match.group(2).lower()
            approvals[f"Change #{change_num}"] = decision == "yes"

    # Get hunks from diff
    _, hunks = add_change_numbers(diff, file_path)
    hunk_pattern = re.compile(r'^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,(\d+))? @@(?: .*)?$')

    # Build merged content
    merged_lines = file_lines.copy()
    for hunk in hunks:
        change_num = hunk["number"]
        if change_num not in approvals:
            continue  # Skip if no decision for this change

        # Extract line numbers
        header = hunk["header"]
        hunk_match = hunk_pattern.match(header)
        if not hunk_match:
            continue
        new_start = int(hunk_match.group(2)) - 1  # 0-based
        new_lines = int(hunk_match.group(3)) if hunk_match.group(3) else 1

        # Get diff lines
        diff_lines = hunk["content"].splitlines()
        added_lines = [line[1:] for line in diff_lines if line.startswith('+')]
        removed_lines = [line[1:] for line in diff_lines if line.startswith('-')]

        # Apply or revert based on decision
        if approvals[change_num]:  # Yes: apply added lines
            merged_lines[new_start:new_start + new_lines] = added_lines
        else:  # No: keep removed lines
            merged_lines[new_start:new_start + new_lines] = removed_lines

    return "\n".join(merged_lines)

if __name__ == '__main__':
    path = Path("/home/charlie/test_git_diff/thing.txt")
    diff, error = get_git_diff(path)
    if error:
        print(f"Error: {error}")
    else:
        # Print diff for LLM
        modified_diff, hunks = add_change_numbers(diff, path)
        print("Diff for LLM:\n")
        print(modified_diff)
        print("\nHunks:", hunks)
        
        # Hardcoded LLM response for testing (matches 5 changes)
        llm_response = """Change #1, Yes
Change #2, No
Change #3, Yes
Change #4, Yes
Change #5, No"""
        
        print("\nLLM Response:\n")
        print(llm_response)
        
        # Apply changes and print merged content
        merged_content = apply_changes(path, diff, llm_response)
        print("\nMerged File Content:\n")
        print(merged_content)