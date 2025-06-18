import subprocess
import os
import re
from pathlib import Path
from typing import List

from assistant_merger.git_tools import get_git_diff, add_change_numbers, apply_changes

# Special marker to identify AI responses
AI_MARKER = "<AI_RESPONSE>"

def run_bash_commands(commands):
    try:
        result = subprocess.run(commands, shell=True, capture_output=True, text=True)
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)

# Function to save a file
def save_file(path, content):
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
        # Get git diff using git_tools
        diff, error = get_git_diff(Path(path))
        if error:
            return f"Saved file: {path}\n{error}\n{read_file(path)}"
        # Generate hunk choices
        modified_diff, hunks = add_change_numbers(diff, Path(path), add_line_numbers=True)
        choices = [f"{hunk['number']}, (Yes/No)" for hunk in hunks]
        choices_output = f"### AI_CHOICES_START: {path} ###\n" + "\n".join(choices) + "\n### AI_CHOICES_END ###" if hunks else ""
        return f"Saved file: {path}\n{modified_diff}\n{choices_output}"
    except Exception as e:
        return str(e)

# Function to read directory contents with regex filtering
def read_directory(directory, regex):
    try:
        pattern = re.compile(regex)
        output = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if pattern.match(file):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        content = f.read()
                    output.append(f"--- File: {file_path} ---\n{content}\n--- End of file ---")
        return "\n".join(output)
    except Exception as e:
        return str(e)

# Function to read a single file
def read_file(path, add_line_numbers: bool = True):
    try:
        with open(path, 'r') as f:
            content = f.read()
        if add_line_numbers:
            lines = content.splitlines()
            numbered_lines = [f"{i+1:4d} {line}" for i, line in enumerate(lines)]
            content = "\n".join(numbered_lines)
        return f"--- File: {path} ---\n{content}\n--- End of file ---"
    except Exception as e:
        return str(e)

# Function to read specific lines from a file
def read_lines(file_path: str, start: int, end: int, prefix: str = "") -> list[str]:
    try:
        with open(file_path, 'r') as f:
            file = f.read()
        lines = file.split("\n")
        # Adjust for 1-based indexing and slice
        selected_lines = lines[start-1:end]
        # Apply prefix (e.g., indent) or remove prefix if negative
        if prefix.startswith("-"):
            remove_str = prefix[1:]
            remove_str_len = len(remove_str)
            selected_lines = [line[remove_str_len:] if line.startswith(remove_str) else line for line in selected_lines]
        elif prefix.startswith("+"):
            add_str = prefix[1:]
            selected_lines = [add_str+line for line in selected_lines]
        print(selected_lines)
        return selected_lines
    except Exception as e:
        return [f"Error reading lines {start}-{end} from {file_path}: {e}"]

def process_commands(input_text: str) -> str:
    output_lines = []
    if input_text.startswith(AI_MARKER):
        # AI input: process commands
        input_text = input_text[len(AI_MARKER):].strip()
        lines = input_text.splitlines()
        in_bash = False
        in_save = False
        in_apply_choices = False
        current_path = None
        bash_commands = []
        save_content = []
        choices_content = []

        read_lines_pattern = re.compile(r'^\s*### AI_READ_LINES: (.+?):(\d+):(\d+)(?::"(.+?)")? ###$')

        for line in lines:
            if line.strip() == "### AI_BASH_START ###":
                if in_bash:
                    output_lines.append("Error: Nested bash start")
                else:
                    in_bash = True
                    bash_commands = []
            elif line.strip() == "### AI_BASH_END ###":
                if in_bash:
                    in_bash = False
                    commands = "\n".join(bash_commands)
                    output_lines.append(run_bash_commands(commands))
                else:
                    output_lines.append("Error: Bash end without start")
            elif in_bash:
                bash_commands.append(line)
            elif line.startswith("### AI_SAVE_START: "):
                if in_save:
                    output_lines.append("Error: Nested save start")
                else:
                    in_save = True
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        current_path = parts[1].strip().rstrip(" ###")
                        save_content = []
                    else:
                        output_lines.append("Error: Invalid save start format")
            elif line.strip() == "### AI_SAVE_END ###":
                if in_save:
                    in_save = False
                    content = "\n".join(save_content)
                    output_lines.append(save_file(current_path, content))
                    current_path = None
                else:
                    output_lines.append("Error: Save end without start")
            elif in_save:
                read_lines_match = read_lines_pattern.match(line)
                if read_lines_match:
                    file_path = read_lines_match.group(1)
                    start = int(read_lines_match.group(2))
                    end = int(read_lines_match.group(3))
                    prefix = read_lines_match.group(4) or ""
                    save_content.extend(read_lines(file_path, start, end, prefix))
                else:
                    save_content.append(line)
            elif line.startswith("### AI_APPLY_CHOICES: "):
                if in_apply_choices:
                    output_lines.append("Error: Nested apply choices start")
                else:
                    in_apply_choices = True
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        current_path = parts[1].strip().rstrip(" ###")
                        choices_content = []
                    else:
                        output_lines.append("Error: Invalid apply choices format")
            elif line.strip() == "### AI_APPLY_CHOICES_END ###":
                if in_apply_choices:
                    in_apply_choices = False
                    diff, error = get_git_diff(Path(current_path))
                    if error:
                        output_lines.append(f"Error: {error}")
                    else:
                        llm_response = "\n".join(choices_content)
                        merged_content = apply_changes(Path(current_path), diff, llm_response)
                        output_lines.append(save_file(current_path, merged_content))
                    current_path = None
                else:
                    output_lines.append("Error: Apply choices end without start")
            elif in_apply_choices:
                choices_content.append(line)
            elif line.startswith("### AI_READ_DIR: "):
                parts = line.split("regex:", 1)
                if len(parts) == 2:
                    dir_path = parts[0].split(":", 1)[1].strip()
                    regex = parts[1].strip().rstrip(" ###")
                    output_lines.append(read_directory(dir_path, regex))
                else:
                    output_lines.append("Error: Invalid read_dir format")
            elif line.startswith("### AI_READ_FILE: "):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    file_path = parts[1].strip().rstrip(" ###")
                    output_lines.append(read_file(file_path))
                else:
                    output_lines.append("Error: Invalid read_file format")

        # Check for unclosed blocks
        if in_bash:
            output_lines.append("Error: Unclosed bash block")
        if in_save:
            output_lines.append("Error: Unclosed save block")
        if in_apply_choices:
            output_lines.append("Error: Unclosed apply choices block")
    return "\n".join(output_lines)


