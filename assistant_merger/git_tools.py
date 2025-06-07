import os
import subprocess
import re
from pathlib import Path
from typing import Optional, Tuple, List, Dict

def find_git_repo(file_path: Path) -> Optional[Path]:
    current = file_path.parent
    while current != current.parent:
        if (current / ".git").is_dir():
            return current
        current = current.parent
    return None

def get_git_diff(file_path: Path) -> Tuple[str, Optional[str]]:
    repo_path = find_git_repo(file_path)
    if not repo_path:
        return "", f"No git repository found for {file_path}"
    try:
        relative_path = file_path.relative_to(repo_path)
        result = subprocess.run(
            ["git", "diff", "--unified=1", str(relative_path)],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            return result.stdout, None
        return "", f"No changes or file not tracked: {relative_path}"
    except subprocess.SubprocessError as e:
        return "", f"Error running git diff: {e}"
    except ValueError as e:
        return "", f"Invalid file path relative to repo: {e}"

def add_change_numbers(diff: str) -> Tuple[str, List[Dict[str, str]]]:
    lines = diff.splitlines()
    modified_lines = []
    change_count = 0
    hunks = []
    current_hunk_lines = []
    hunk_start = None

    for line in lines:
        if re.match(r"@@ -\d+,\d+ \+\d+,\d+ @@", line):
            if current_hunk_lines and hunk_start:
                hunks.append({
                    "number": f"change_{change_count}",
                    "header": hunk_start,
                    "content": "\n".join(current_hunk_lines)
                })
                current_hunk_lines = []
            change_count += 1
            hunk_start = line
            modified_lines.append(f"{line} (Change #{change_count})")
        else:
            current_hunk_lines.append(line)
            modified_lines.append(line)

    if current_hunk_lines and hunk_start:
        hunks.append({
            "number": f"change_{change_count}",
            "header": hunk_start,
            "content": "\n".join(current_hunk_lines)
        })

    return "\n".join(modified_lines), hunks

def apply_changes(file_path: Path, diff: str, model_response: str) -> bool:
    try:
        with file_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        actions = []
        for line in model_response.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=2)
            if len(parts) < 2:
                continue
            action, change_id = parts[0].lower(), parts[1]
            content = parts[2] if len(parts) > 2 and action == "merge" else ""
            actions.append({"action": action, "change_id": change_id, "content": content})

        _, hunks = add_change_numbers(diff)

        line_changes = []
        for hunk in hunks:
            header = hunk["header"]
            match = re.match(r"@@ -(\d+),(\d+) \+(\d+),(\d+) @@", header)
            if not match:
                print(f"Warning: Invalid hunk header: {header}")
                continue
            old_start, old_count, new_start, new_count = map(int, match.groups())
            added_lines = sum(1 for line in hunk["content"].splitlines() if line.startswith("+"))
            line_changes.append({
                "hunk": hunk,
                "old_start": old_start - 1,
                "old_count": old_count,
                "new_start": new_start - 1,
                "new_count": added_lines
            })

        line_changes.sort(key=lambda x: x["new_start"], reverse=True)

        for change in line_changes:
            hunk = change["hunk"]
            change_id = hunk["number"]
            action = next((a for a in actions if a["change_id"] == change_id), None)
            start = change["new_start"]
            end = start + change["new_count"]
            print(f"Processing {change_id}: action={action}, start={start}, end={end}")
            if action and action["action"] == "reject":
                if change["old_count"] == 0:
                    lines[start:start + change["new_count"]] = []
                else:
                    hunk_lines = [line[1:] for line in hunk["content"].splitlines() if line.startswith("-")]
                    lines[start:end] = hunk_lines or []
                print(f"Reverted {change_id}")
            elif action and action["action"] == "merge" and action["content"]:
                lines[start:start + change["new_count"]] = action["content"].splitlines(keepends=True)
                print(f"Merged {change_id}")
            else:
                print(f"Accepted {change_id}")

        with file_path.open("w", encoding="utf-8") as f:
            f.writelines(lines)
        return True
    except Exception as e:
        print(f"Error applying changes to {file_path}: {e}")
        return False