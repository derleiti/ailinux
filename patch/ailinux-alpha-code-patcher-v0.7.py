#!/usr/bin/env python3
"""
PyLint Issue Fixer for AILinux

This script automatically fixes common PyLint issues in Python code, including:
1. Syntax errors (E0001) - most critical!
2. Missing docstrings (C0111, C0112)
3. Trailing whitespace (C0303)
4. Long lines (C0301)
5. Improper string formatting in logging calls (W1203)
6. Unused imports (W0611)

Usage:
    python improved-pylint-fixes.py [--dry-run] [--log-file FILE] [--optimization-log FILE]
"""
import os
import re
import sys
import argparse
import logging
from typing import List, Dict, Tuple, Optional, Any


class PylintIssue:
    """Represents a pylint issue from the log file."""

    def __init__(self, file_path: str, line_num: int, code: str, message: str):
        """Initialize a new pylint issue.
        
        Args:
            file_path: Path to the file with the issue
            line_num: Line number where the issue occurs
            code: PyLint error/warning code (e.g., C0303)
            message: Description of the issue
        """
        self.file_path = file_path
        self.line_num = line_num
        self.code = code  # e.g. C0303, E0611
        self.message = message

    def __repr__(self) -> str:
        """Return a string representation of the issue."""
        return f"{self.file_path}:{self.line_num} [{self.code}] {self.message}"


class CodeFixer:
    """Class for fixing pylint issues in code."""

    def __init__(self, issues: List[PylintIssue], dry_run: bool = False,
                 log_file: Optional[str] = None, verbose: bool = False):
        """Initialize the code fixer.
        
        Args:
            issues: List of pylint issues to fix
            dry_run: If True, don't actually modify files
            log_file: Path to write log output to
            verbose: Whether to print detailed logs
        """
        self.issues = issues
        self.dry_run = dry_run
        self.verbose = verbose
        self.file_cache: Dict[str, List[str]] = {}
        self.fixes_applied = 0
        self.skipped_issues = 0
        self.fixed_issues: List[PylintIssue] = []
        self.unfixed_issues: List[PylintIssue] = []
        self.files_modified: List[str] = []

        # Setup logging
        self.logger = logging.getLogger('pylint_fixer')

        # Set log level based on verbose flag
        log_level = logging.DEBUG if verbose else logging.INFO
        self.logger.setLevel(log_level)

        # Console handler
        console = logging.StreamHandler()
        console.setLevel(log_level)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        console.setFormatter(formatter)
        self.logger.addHandler(console)

        # File handler (if log_file is provided)
        if log_file:
            file_handler = logging.FileHandler(log_file, mode='w')
            file_handler.setLevel(logging.DEBUG)  # Always detailed in the file
            file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def load_file(self, file_path: str) -> List[str]:
        """Load a file into the cache if it's not already loaded.
        
        Args:
            file_path: Path to the file to load
            
        Returns:
            List of lines from the file
        """
        if file_path not in self.file_cache:
            if not os.path.exists(file_path):
                self.logger.warning("File not found: %s", file_path)
                return []

            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    self.file_cache[file_path] = file.readlines()
            except UnicodeDecodeError:
                # Try again with latin-1 encoding if utf-8 fails
                with open(file_path, 'r', encoding='latin-1') as file:
                    self.file_cache[file_path] = file.readlines()

        return self.file_cache[file_path]

    def save_file(self, file_path: str) -> None:
        """Save the modified file contents.
        
        Args:
            file_path: Path to the file to save
        """
        if self.dry_run:
            self.logger.info("[DRY RUN] Would save %s", file_path)
        else:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.writelines(self.file_cache[file_path])
                self.logger.info("Saved: %s", file_path)
                if file_path not in self.files_modified:
                    self.files_modified.append(file_path)
            except Exception as e:
                self.logger.error("Error saving %s: %s", file_path, e)

    def fix_unused_import(self, issue: PylintIssue) -> bool:
        """Remove unused imports (W0611).
        
        Args:
            issue: The pylint issue to fix
            
        Returns:
            True if the issue was fixed, False otherwise
        """
        lines = self.load_file(issue.file_path)
        if not lines:
            return False

        line = lines[issue.line_num - 1]

        # Extract the unused # Potential unused import: import name from the message
        match = re.search(r"Unused import (\w+)", issue.message)
        if not match:
            return False

        unused_import = match.group(1)

        # Handle different # Potential unused import: import styles
        if re.match(rf"^\s*import\s+{unused_import}\s*$", line):
            # Direct # Potential unused import: import (import unused)
            lines[issue.line_num - 1] = f"# {line.rstrip()}  # removed: {issue.code}\n"
            return True
        elif re.match(rf"^\s*from\s+[\w.]+\s+import\s+{unused_import}\s*$", line):
            # Single # Potential unused import: import from module (from module import unused)
            lines[issue.line_num - 1] = f"# {line.rstrip()}  # removed: {issue.code}\n"
            return True
        elif re.search(rf"from\s+[\w.]+\s+import\s+[^,]+,\s*{unused_import}(\s*,|$)", line):
            # Part of a multi-import (from module import used, unused, other)
            if re.search(rf"{unused_import},", line):
                # Unused # Potential unused import: import followed by comma
                lines[issue.line_num - 1] = line.replace(f"{unused_import}, ", "")
                return True
            elif re.search(rf",\s*{unused_import}", line):
                # Unused # Potential unused import: import preceded by comma
                lines[issue.line_num - 1] = line.replace(f", {unused_import}", "")
                return True

        return False

    def fix_trailing_whitespace(self, issue: PylintIssue) -> bool:
        """Remove trailing whitespace (C0303).
        
        Args:
            issue: The pylint issue to fix
            
        Returns:
            True if the issue was fixed, False otherwise
        """
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
        """Add missing docstrings (C0111, C0112, C0103).
        
        Args:
            issue: The pylint issue to fix
            
        Returns:
            True if the issue was fixed, False otherwise
        """
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
            module_name = os.path.basename(issue.file_path).replace('.py', '')
            module_name = module_name.replace('_', ' ').title()
            docstring = f'"""
                "{module_name} module for AILinux.\n\nThis module provides functionality for the AILinux system.\n"""\n'
            lines.insert(0, docstring)
            return True
        elif is_func and "def " in line:
            # Function docstring
            func_name = re.search(r'def\s+(\w+)', line)
            if func_name:
                name = func_name.group(1)
                docstring = f'{indent_str}"""
                    "\n{indent_str}Description for function {name}.\n{indent_str}"""\n'
                lines.insert(issue.line_num, docstring)
                return True
        elif is_class and "class " in line:
            # Class docstring
            class_name = re.search(r'class\s+(\w+)', line)
            if class_name:
                name = class_name.group(1)
                docstring = f'{indent_str}"""
                    "\n{indent_str}Description for class {name}.\n{indent_str}"""\n'
                lines.insert(issue.line_num, docstring)
                return True

        return False

    def fix_line_too_long(self, issue: PylintIssue) -> bool:
        """Shorten lines that are too long (C0301).
        
        Args:
            issue: The pylint issue to fix
            
        Returns:
            True if the issue was fixed, False otherwise
        """
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

            # Case 1: Fix string concatenation with "+" at the end of line
            if '+" +' in line:
                # There's already a string concatenation, but it's broken
                fixed_line = line.replace('+" +', '"+\n')
                lines[issue.line_num - 1] = fixed_line
                return True

            # Case 2: Try to break a string
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

            # Case 3: Try to break at commas (lists, function parameters)
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

    def fix_f_string_logging(self, issue: PylintIssue) -> bool:
        """Fix f-string usage in logging calls (W1203, W1201).
        
        Args:
            issue: The pylint issue to fix
            
        Returns:
            True if the issue was fixed, False otherwise
        """
        if ("lazy % formatting in logging functions" not in issue.message and
            "logging-fstring-interpolation" not in issue.message and
            "logging-not-lazy" not in issue.message):
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

    def fix_syntax_error_string_concat(self, issue: PylintIssue) -> bool:
        """Fix E0001 syntax errors related to improper string concatenation.
        
        Args:
            issue: The pylint issue to fix
            
        Returns:
            True if the issue was fixed, False otherwise
        """
        if "E0001" not in issue.code:
            return False

        lines = self.load_file(issue.file_path)
        if not lines:
            return False

        line = lines[issue.line_num - 1]

        # Check for issues with string concatenation
        if '=" +' in line or '"" +' in line:
            # Fix multiline string concatenation
            fixed_line = line.replace('=" +', '="')
            fixed_line = fixed_line.replace('"" +', '"')
            lines[issue.line_num - 1] = fixed_line
            return True

        # Check for issues with invalid syntax
        if "invalid syntax" in issue.message and "+" in line:
            # Try to fix broken string concatenation
            if re.search(r'"\s*\+\s*$', line):
                # Line ends with +, join with next line
                next_line = lines[issue.line_num] if issue.line_num < len(lines) else ""
                if next_line and next_line.lstrip().startswith('"'):
                    # Remove + from current line and merge with next
                    lines[issue.line_num - 1] = re.sub(r'"\s*\+\s*$', '"', line)
                    return True

        # Check for unclosed strings
        if "unterminated string literal" in issue.message:
            # Count quotes to see if they're balanced
            single_quotes = line.count("'")
            double_quotes = line.count('"')

            if single_quotes % 2 == 1:  # Odd number of single quotes
                # Try to add the missing quote
                if not line.strip().endswith("'"):
                    lines[issue.line_num - 1] = line.rstrip() + "'\n"
                    return True

            if double_quotes % 2 == 1:  # Odd number of double quotes
                # Try to add the missing quote
                if not line.strip().endswith('"'):
                    lines[issue.line_num - 1] = line.rstrip() + '"\n'
                    return True

        return False

    def fix_function_block_indentation(self, issue: PylintIssue) -> bool:
        """Fix E0001 syntax errors related to missing indentation after function definition.
        
        Args:
            issue: The pylint issue to fix
            
        Returns:
            True if the issue was fixed, False otherwise
        """
        if "E0001" not in issue.code or "expected an indented block" not in issue.message:
            return False

        lines = self.load_file(issue.file_path)
        if not lines:
            return False

        line_num = issue.line_num

        # Check if the previous line is a function or class definition
        prev_line = lines[line_num - 2] if line_num > 1 else ""

        if (("def " in prev_line or "class " in prev_line) and
            prev_line.rstrip().endswith(':')):
            # Add a pass statement with proper indentation
            indent = len(prev_line) - len(prev_line.lstrip()) + 4  # 4 spaces for indentation
            lines.insert(line_num - 1, ' ' * indent + 'pass\n')
            return True

        return False

    def fix_issues(self) -> int:
        """Fix all found issues and return the number of fixed problems.
        
        Returns:
            Number of issues fixed
        """
        # Sort issues by file and line number
        self.issues.sort(key=lambda x: (x.file_path, x.line_num))

        # Group issues by file
        issues_by_file: Dict[str, List[PylintIssue]] = {}
        for issue in self.issues:
            if issue.file_path not in issues_by_file:
                issues_by_file[issue.file_path] = []
            issues_by_file[issue.file_path].append(issue)

        # Print summary of issues to fix
        self.logger.info("Found %s issues in %s files", len(self.issues), len(issues_by_file))

        # Process all issues
        processed_count = 0
        for issue in self.issues:
            processed_count += 1
            if processed_count % 20 == 0:
                self.logger.info("Processing issue %s/%s...", processed_count, len(self.issues))

            fixed = False

            # Try syntax errors first (most critical)
            if "E0001" in issue.code:
                fixed = (self.fix_syntax_error_string_concat(issue) or
                         self.fix_function_block_indentation(issue))

                if fixed and self.verbose:
                    self.logger.debug("Fixed syntax error in %s:%s", issue.file_path, issue.line_num)

            # If syntax error wasn't fixed, try other fixes based on error code
            if not fixed:
                if issue.code == "W0611":  # Unused import
                    fixed = self.fix_unused_import(issue)
                elif issue.code == "C0303":  # Trailing whitespace
                    fixed = self.fix_trailing_whitespace(issue)
                elif issue.code in ["C0111", "C0112", "C0116"]:  # Missing docstring
                    fixed = self.fix_missing_docstring(issue)
                elif issue.code == "C0301":  # Line too long
                    fixed = self.fix_line_too_long(issue)
                elif issue.code in ["W1201", "W1203"]:  # Logging format
                    fixed = self.fix_f_string_logging(issue)

            if fixed:
                self.fixes_applied += 1
                self.fixed_issues.append(issue)
                if self.verbose:
                    self.logger.debug("Fixed: %s", issue)
            else:
                self.skipped_issues += 1
                self.unfixed_issues.append(issue)
                if self.verbose:
                    self.logger.debug("Skipped: %s", issue)

        # Save all modified files
        for file_path in self.file_cache:
            self.save_file(file_path)

        return self.fixes_applied

    def print_summary(self):
        """Print a summary of the fixes applied."""
        print("\n" + "="*50)
        print("SUMMARY:")
        print(f"Total issues processed: {len(self.issues)}")
        print(f"Fixed: {self.fixes_applied} issues")
        print(f"Skipped: {self.skipped_issues} issues")
        print(f"Files modified: {len(self.files_modified)}")

        if self.files_modified:
            print("\nModified files:")
            for file in self.files_modified:
                print(f"  - {file}")

        # Group unfixed issues by code for better overview
        unfixed_by_code: Dict[str, int] = {}
        for issue in self.unfixed_issues:
            if issue.code not in unfixed_by_code:
                unfixed_by_code[issue.code] = 0
            unfixed_by_code[issue.code] += 1

        if unfixed_by_code:
            print("\nUnfixed issues by type:")
            for code, count in sorted(unfixed_by_code.items(), key=lambda x: x[1], reverse=True):
                print(f"  {code}: {count} issues")


def parse_pylint_log(log_path: str) -> List[PylintIssue]:
    """Parse the pylint log file and extract issues.
    
    Args:
        log_path: Path to the pylint log file
        
    Returns:
        List of parsed pylint issues
    """
    issues = []

    try:
        with open(log_path, 'r', encoding='utf-8') as file:
            for line in file:
                # Typical pylint format: file.py:42:0: C0111: Missing docstring (missing-docstring)
                match = re.match(r'
                    "^([\w\./\-]+):(\d+)(?::\d+)?: ([CRWE]\d{4}): (.+?)(?:\s\([\w-]+\))?$', line.strip())
                if match:
                    file_path, line_num, code, message = match.groups()
                    issues.append(PylintIssue(
                        file_path=file_path,
                        line_num=int(line_num),
                        code=code,
                        message=message
                    ))
    except (FileNotFoundError, UnicodeDecodeError) as e:
        print(f"Error reading log file {log_path}: {e}")
        sys.exit(1)

    return issues


def main():
    """Main function to parse arguments and run the fixer.
    
    Returns:
        Exit code: 0 for success, 1 for error
    """
    parser = argparse.ArgumentParser(
        description='Fix common pylint issues automatically')

    parser.add_argument('--log-file', '-l',
                      help='Path to write detailed log output',
                      default='pylint_fixed.log')

    parser.add_argument('--optimization-log', '-o',
                      help='Path to the pylint log file (default: optimization.log)',
                      default='optimization.log')

    parser.add_argument('--dry-run', '-d', action='store_true',
                      help='Show changes without applying them')

    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Print detailed output')

    parser.add_argument('--version', action='version',
                      version='%(prog)s 1.0')

    args = parser.parse_args()

    # Check if log file exists
    if not os.path.exists(args.optimization_log):
        print(f"Error: The pylint log file {args.optimization_log} does not exist.")
        return 1

    print(f"Analyzing {args.optimization_log}...")
    issues = parse_pylint_log(args.optimization_log)

    if not issues:
        print("No issues found in the log file.")
        return 0

    print(f"Found {len(issues)} issues to fix.")

    # Create and run the CodeFixer
    fixer = CodeFixer(
        issues,
        dry_run=args.dry_run,
        log_file=args.log_file,
        verbose=args.verbose
    )

    try:
        # Fix the issues
        fixes_applied = fixer.fix_issues()

        # Print summary
        fixer.print_summary()

        # Print advice
        if fixes_applied > 0:
            print("\nAdvice:")
            print("  1. Run pylint again to see if any issues remain")
            print("  2. Some issues may require manual intervention")
            print("  3. Review the changes made by this script")

        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
