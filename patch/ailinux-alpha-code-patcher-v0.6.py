#!/usr/bin/env python3
"""
PyLint Issue Fixer

This script automatically fixes common PyLint issues in Python code, including:
1. Missing docstrings
2. Trailing whitespace
3. Long lines
4. Missing encodings in open() calls
5. Unused imports
6. Improper string formatting in logging calls

Usage:
    python pylint_fixer.py [file_or_directory]
"""
import os
import re
import sys
import argparse
from typing import List, Dict, Tuple, Optional, Any


class PylintIssue:
    """Represents a pylint issue from the log file."""

    def __init__(self, file_path: str, line_num: int, code: str, message: str):
        self.file_path = file_path
        self.line_num = line_num
        self.code = code  # e.g. C0103, E0611
        self.message = message

    def __repr__(self) -> str:
        return f"{self.file_path}:{self.line_num} [{self.code}] {self.message}"


class CodeFixer:
    """Class for fixing pylint issues in code."""

    def __init__(self, issues: List[PylintIssue], dry_run: bool = False, log_file: str = None):
        self.issues = issues
        self.dry_run = dry_run
        self.file_cache: Dict[str, List[str]] = {}
        self.fixes_applied = 0
        self.skipped_issues = 0
        self.fixed_issues: List[PylintIssue] = []
        self.unfixed_issues: List[PylintIssue] = []

        # Setup logging
        import logging
        self.logger = logging.getLogger('pylint_fixer')
        self.logger.setLevel(logging.INFO)

        # Console handler
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        self.logger.addHandler(console)

        # File handler (if log_file is provided)
        if log_file:
            file_handler = logging.FileHandler(log_file, mode='w')
            file_handler.setLevel(logging.INFO)
            self.logger.addHandler(file_handler)

    def load_file(self, file_path: str) -> List[str]:
        """Loads a file into the cache if it's not already loaded."""
        if file_path not in self.file_cache:
            if not os.path.exists(file_path):
                self.logger.warning("File not found: %sfile_path")
                return []

            with open(file_path, 'r', encoding='utf-8') as file:
                self.file_cache[file_path] = file.readlines()
        return self.file_cache[file_path]

    def save_file(self, file_path: str) -> None:
        """Saves the modified file contents."""
        if self.dry_run:
            self.logger.info("[DRY RUN] Would save %sfile_path")
        else:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(self.file_cache[file_path])
            self.logger.info("Saved: %sfile_path")

    def fix_unused_import(self, issue: PylintIssue) -> bool:
        """Removes unused imports (W0611)."""
        lines = self.load_file(issue.file_path)
        if not lines:
            return False

        line = lines[issue.line_num - 1]

        # Extract the unused import name from the message
        match = re.search(r"Unused import (\w+)", issue.message)
        if not match:
            return False

        unused_import = match.group(1)

        # Handle different import styles
        if re.match(rf"^\s*import\s+{unused_import}\s*$", line):
            # Direct import (import unused)
            lines[issue.line_num - 1] = f"# {line}  # removed: {issue.code}\n"
            return True
        elif re.match(rf"^\s*from\s+[\w.]+\s+import\s+{unused_import}\s*$", line):
            # Single import from module (from module import unused)
            lines[issue.line_num - 1] = f"# {line}  # removed: {issue.code}\n"
            return True
        elif re.search(rf"from\s+[\w.]+\s+import\s+[^,]+,\s*{unused_import}(\s*,|$)", line):
            # Part of a multi-import (from module import used, unused, other)
            if re.search(rf"{unused_import},", line):
                # Unused import followed by comma
                lines[issue.line_num - 1] = line.replace(f"{unused_import}, ", "")
                return True
            elif re.search(rf",\s*{unused_import}", line):
                # Unused import preceded by comma
                lines[issue.line_num - 1] = line.replace(f", {unused_import}", "")
                return True

        return False

    def fix_trailing_whitespace(self, issue: PylintIssue) -> bool:
        """Removes trailing whitespace (C0303)."""
        lines = self.load_file(issue.file_path)
        if not lines:
            return False

        line = lines[issue.line_num - 1]
        fixed_line = line.rstrip() + '\n'

        if fixed_line != line:
            lines[issue.line_num - 1] = fixed_line
            return True

        return False

    def fix_missing_docstring(self, issue: PylintIssue) -> bool:
        """Adds missing docstrings (C0111, C0112, C0103)."""
        if not ("Missing docstring" in issue.message or "docstring" in issue.message.lower()):
            return False

        lines = self.load_file(issue.file_path)
        if not lines:
            return False

        line = lines[issue.line_num - 1]

        # Detect if it's a function, class, or module
        is_func = "function" in issue.message.lower() or "def " in line
        is_class = "class" in issue.message.lower() or "class " in line
        is_module = "module" in issue.message.lower() or issue.line_num == 1

        indent = len(line) - len(line.lstrip())
        indent_str = ' ' * indent

        if is_module and issue.line_num == 1:
            # Module docstring
            docstring = '"""\nModule docstring missing.\n"""\n'
            lines.insert(0, docstring)
            return True
        elif is_func and "def " in line:
            # Function docstring
            func_name = re.search(r'def\s+(\w+)', line)
            if func_name:
                name = func_name.group(1)
                docstring = f'{indent_str}"""\nDescription for function {name}.\n{indent_str}"""\n'
                lines.insert(issue.line_num, docstring)
                return True
        elif is_class and "class " in line:
            # Class docstring
            class_name = re.search(r'class\s+(\w+)', line)
            if class_name:
                name = class_name.group(1)
                docstring = f'{indent_str}"""\nDescription for class {name}.\n{indent_str}"""\n'
                lines.insert(issue.line_num, docstring)
                return True

        return False

    def fix_line_too_long(self, issue: PylintIssue) -> bool:
        """Shortens lines that are too long (C0301)."""
        if "Line too long" not in issue.message:
            return False

        lines = self.load_file(issue.file_path)
        if not lines:
            return False

        line = lines[issue.line_num - 1]

        # Try to break the line if it's longer than the limit
        match = re.search(r"Line too long \((\d+)/(\d+)\)", issue.message)
        if match:
            current_len = int(match.group(1))
            limit = int(match.group(2))

            if current_len <= limit:
                return False

            # Case 1: Try to break a string
            if '"' in line or "'" in line:
                for quote in ['"', "'"]:
                    pattern = f'({quote}[^{quote}]*{quote})'
                    strings = re.findall(pattern, line)
                    for string in strings:
                        if len(string) > 30:  # Only split long strings
                            indent = len(line) - len(line.lstrip())
                            indent_str = ' ' * (indent + 4)  # Extra indentation
                            replacement = f"{string[0]}\" +\n{indent_str}\"{string[1:-1]}{string[-1]}"
                            new_line = line.replace(string, replacement)
                            lines[issue.line_num - 1] = new_line
                            return True

            # Case 2: Try to break at commas (lists, function parameters)
            if ',' in line and not ('"' in line or "'" in line):  # Avoid breaking inside strings
                parts = line.split(',')
                if len(parts) > 1:
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * indent
                    new_lines = [parts[0] + ',']
                    for part in parts[1:-1]:
                        new_lines.append(indent_str + part.strip() + ',')
                    new_lines.append(indent_str + parts[-1].strip())
                    lines[issue.line_num - 1] = new_lines[0] + '\n'
                    for i, new_line in enumerate(new_lines[1:], start=1):
                        lines.insert(issue.line_num - 1 + i, new_line + '\n')
                    return True

        return False

    def fix_missing_encoding(self, issue: PylintIssue) -> bool:
        """Add encoding parameter to open() calls (W1514)."""
        if "open without explicitly specifying an encoding" not in issue.message:
            return False

        lines = self.load_file(issue.file_path)
        if not lines:
            return False

        line = lines[issue.line_num - 1]

        # Look for open() calls without encoding
        match = re.search(r'open\(\s*([^,)]+)(?:\s*,\s*([^,)]+))?\s*\)', line)
        if match:
            if match.group(2) and "encoding" in match.group(2):
                # Encoding already specified
                return False

            # Replace the open call with one that includes encoding
            if match.group(2):
                # There's a second parameter (probably mode)
                replacement = f'open({match.group(1)}, {match.group(2)}, encoding=\'utf-8\')'
            else:
                # Only filepath parameter
                replacement = f'open({match.group(1)}, encoding=\'utf-8\')'

            new_line = line.replace(match.group(0), replacement)
            lines[issue.line_num - 1] = new_line
            return True

        return False

    def fix_f_string_logging(self, issue: PylintIssue) -> bool:
        """Fix f-string usage in logging calls (W1203)."""
        if "lazy % formatting in logging functions" not in issue.message:
            return False

        lines = self.load_file(issue.file_path)
        if not lines:
            return False

        line = lines[issue.line_num - 1]

        # Regular expression to find logging calls with f-strings
        match = re.search(r'(logger\.\w+)\(f[\'"](.+?)[\'"](,.+?)?\)', line)
        if match:
            log_call = match.group(1)
            f_string_content = match.group(2)
            args = match.group(3) if match.group(3) else ''

            # Replace f-string with % formatting
            f_string_content = f_string_content.replace('{', '%s').replace('}', '')
            new_line = f'{log_call}("{f_string_content}"{args})'
            lines[issue.line_num - 1] = line.replace(match.group(0), new_line)
            return True

        return False

    def fix_issues(self) -> int:
        """Fix all found issues and return the number of fixed problems."""
        # Group issues by file to process multiple changes to the same file efficiently
        issues_by_file: Dict[str, List[PylintIssue]] = {}
        for issue in self.issues:
            if issue.file_path not in issues_by_file:
                issues_by_file[issue.file_path] = []
            issues_by_file[issue.file_path].append(issue)

        # Process all issues
        for issue in self.issues:
            fixed = False

            # Select appropriate fixer based on pylint code
            if issue.code == "W0611":  # Unused import
                fixed = self.fix_unused_import(issue)
            elif issue.code == "C0303":  # Trailing whitespace
                fixed = self.fix_trailing_whitespace(issue)
            elif issue.code in ["C0111", "C0112", "C0116"]:  # Missing docstring
                fixed = self.fix_missing_docstring(issue)
            elif issue.code == "C0301":  # Line too long
                fixed = self.fix_line_too_long(issue)
            elif issue.code == "W1514":  # Missing encoding
                fixed = self.fix_missing_encoding(issue)
            elif issue.code in ["W1201", "W1203"]:  # Logging format
                fixed = self.fix_f_string_logging(issue)

            if fixed:
                self.fixes_applied += 1
                self.fixed_issues.append(issue)
                self.logger.info("Fixed: %sissue")
            else:
                self.skipped_issues += 1
                self.unfixed_issues.append(issue)
                self.logger.info("Skipped: %sissue")

        # Save all modified files
        for file_path in self.file_cache:
            self.save_file(file_path)

        # Create a summary
        self.logger.info("\n" + "="*50)
        self.logger.info("SUMMARY:")
        self.logger.info("Total issues processed: %slen(self.issues)")
        self.logger.info("Fixed: %sself.fixes_applied issues")
        self.logger.info("Skipped: %sself.skipped_issues issues")

        # Group unfixed issues by code for better overview
        unfixed_by_code: Dict[str, int] = {}
        for issue in self.unfixed_issues:
            if issue.code not in unfixed_by_code:
                unfixed_by_code[issue.code] = 0
            unfixed_by_code[issue.code] += 1

        if unfixed_by_code:
            self.logger.info("\nUnfixed issues by type:")
            for code, count in sorted(unfixed_by_code.items(), key=lambda x: x[1], reverse=True):
                self.logger.info("  %scode: %scount issues")

        return self.fixes_applied


def parse_pylint_log(log_path: str) -> List[PylintIssue]:
    """Parse the pylint log file and extract issues."""
    issues = []

    with open(log_path, 'r', encoding='utf-8') as file:
        for line in file:
            # Typical pylint format: file.py:42:0: C0111: Missing docstring (missing-docstring)
            match = re.match(r'" +'"
                "^([\w\./\-]+):(\d+)(?::\d+)?: ([CRWE]\d{4}): (.+?)(?:\s\([\w-]+\))?$', line.strip())
            if match:
                file_path, line_num, code, message = match.groups()
                issues.append(PylintIssue(
                    file_path=file_path,
                    line_num=int(line_num),
                    code=code,
                    message=message
                ))

    return issues


def main():
    """Main function of the program."""
    parser = argparse.ArgumentParser(description='Fix common pylint issues automatically.')
    parser.add_argument('log_file', nargs='?', default='optimization.log',
                        help='Path to the pylint log file (default: optimization.log)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show changes without applying them')
    parser.add_argument('--output-log',
                        help='Path to the output log file (default: pylint_fixes.log)',
                        default='pylint_fixes.log')
    parser.add_argument('--create-patch', action='store_true',
                        help='Create a patch file with all changes')
    args = parser.parse_args()

    if not os.path.exists(args.log_file):
        print(f"Error: The file {args.log_file} does not exist.")
        sys.exit(1)

    print(f"Analyzing {args.log_file}...")
    issues = parse_pylint_log(args.log_file)
    print(f"Found {len(issues)} issues.")

    # Configure logging
    log_file = args.output_log if not args.dry_run else None

    # Create and run the CodeFixer
    fixer = CodeFixer(issues, dry_run=args.dry_run, log_file=log_file)
    fixes = fixer.fix_issues()

    # Create a patch file if requested
    if args.create_patch and not args.dry_run and fixes > 0:
        create_patch_file(fixer.file_cache, "pylint_fixes.patch")

    # Print summary
    mode = "Dry run" if args.dry_run else "Applied"
    print(f"\n{mode}: Fixed {fixes} of {len(issues)} issues.")

    if not args.dry_run:
        print(f"Detailed log written to: {args.output_log}")

    return 0


def create_patch_file(file_cache: Dict[str, List[str]], patch_file: str):
    """Create a patch file with all changes."""
    import difflib
    import time

    with open(patch_file, 'w', encoding='utf-8') as f:
        f.write(f"# Created by pylint_fixer.py on {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        for file_path, lines in file_cache.items():
            try:
                # Load the original file
                with open(file_path, 'r', encoding='utf-8') as original_file:
                    original_lines = original_file.readlines()

                # Create the diff
                diff = difflib.unified_diff(
                    original_lines,
                    lines,
                    fromfile=f"a/{file_path}",
                    tofile=f"b/{file_path}",
                    n=3
                )

                # Write the diff to the patch file
                diff_content = ''.join(diff)
                if diff_content:
                    f.write(diff_content)
                    f.write('\n')
            except Exception as e:
                f.write(f"# Error creating patch for {file_path}: {str(e)}\n\n")


if __name__ == "__main__":
    sys.exit(main())
