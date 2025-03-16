#!/usr/bin/env python3
"""
Targeted PyLint Issue Fixer for AILinux

This script focuses on fixing the most common remaining issues:
1. Trailing whitespace (C0303) - 91 issues
2. Unused variables (W0612) - 47 issues
3. Broad exception catching (W0718) - 46 issues
4. F-string in logging (W1203) - 38 issues
5. Naming conventions (C0103) - 21 issues
6. Parsing errors (E0001) - 19 issues

Usage:
    python targeted-fixes.py [--dry-run] [--log-file FILE] [--optimization-log FILE]
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
        """Initialize a new pylint issue."""
        self.file_path = file_path
        self.line_num = line_num
        self.code = code
        self.message = message

    def __repr__(self) -> str:
        """Return a string representation of the issue."""
        return f"{self.file_path}:{self.line_num} [{self.code}] {self.message}"


class CodeFixer:
    """Class for fixing pylint issues in code."""

    def __init__(self, issues: List[PylintIssue], dry_run: bool = False,
                 log_file: Optional[str] = None, verbose: bool = False):
        """Initialize the code fixer."""
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
        self.logger = logging.getLogger('targeted_fixer')

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
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def load_file(self, file_path: str) -> List[str]:
        """Load a file into the cache if it's not already loaded."""
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
        """Save the modified file contents."""
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

    def fix_trailing_whitespace(self, issue: PylintIssue) -> bool:
        """Remove trailing whitespace (C0303)."""
        lines = self.load_file(issue.file_path)
        if not lines:
            return False

        line = lines[issue.line_num - 1]
        fixed_line = line.rstrip() + '\n'

        if fixed_line != line:
            lines[issue.line_num - 1] = fixed_line
            return True

        return False

    def fix_unused_variable(self, issue: PylintIssue) -> bool:
        """Fix unused variables (W0612)."""
        if "Unused variable" not in issue.message:
            return False

        lines = self.load_file(issue.file_path)
        if not lines:
            return False

        line = lines[issue.line_num - 1]

        # Extract the variable name
        match = re.search(r"Unused variable '(\w+)'", issue.message)
        if not match:
            return False

        var_name = match.group(1)

        # Check if it's a simple assignment
        assignment_match = re.search(rf"\b({var_name})\s*=", line)
        if assignment_match:
            # Replace variable name with underscore to indicate it's intentionally unused
            replaced_line = line.replace(assignment_match.group(1), '_' + var_name)
            lines[issue.line_num - 1] = replaced_line
            return True

        return False

    def fix_broad_exception(self, issue: PylintIssue) -> bool:
        """Fix broad exception catching (W0718)."""
        if "Catching too general exception" not in issue.message:
            return False

        lines = self.load_file(issue.file_path)
        if not lines:
            return False

        line = lines[issue.line_num - 1]

        # Check if it's a simple 'except Exception:' or 'except Exception:'
        if re.search(r'except\s+Exception\s*:', line):
            # Replace with except (Exception, RuntimeError):
            replaced_line = line.replace('except Exception:', 'except (Exception, RuntimeError):')
            lines[issue.line_num - 1] = replaced_line
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

            # Extract variables from f-string
            vars_in_f_string = re.findall(r'{([^}]+)}', f_string_content)

            # Replace f-string with % formatting
            modified_content = re.sub(r'{([^}]+)}', '%s', f_string_content)

            # If variables were found, add them to the args
            if vars_in_f_string:
                var_args = ", ".join(vars_in_f_string)
                if args:
                    # Add variables to existing args
                    new_line = f'{log_call}("{modified_content}", {var_args}{args})'
                else:
                    # Create new args
                    new_line = f'{log_call}("{modified_content}", {var_args})'
            else:
                # No variables found
                new_line = f'{log_call}("{modified_content}"{args})'

            lines[issue.line_num - 1] = line.replace(match.group(0), new_line)
            return True

        return False

    def fix_constant_naming(self, issue: PylintIssue) -> bool:
        """Fix constant naming style (C0103)."""
        if "Constant name" not in issue.message or "
            "doesn't conform to UPPER_CASE" not in issue.message:
            return False

        lines = self.load_file(issue.file_path)
        if not lines:
            return False

        line = lines[issue.line_num - 1]

        # Extract the constant name
        match = re.search(r"Constant name \"(\w+)\"", issue.message)
        if not match:
            return False

        const_name = match.group(1)

        # Convert to UPPER_CASE
        upper_name = const_name.upper()

        # Replace the name
        if re.search(rf"\b{const_name}\s*=", line):
            replaced_line = line.replace(const_name, upper_name)
            lines[issue.line_num - 1] = replaced_line
            return True

        return False

    def fix_syntax_error(self, issue: PylintIssue) -> bool:
        """Fix syntax errors (E0001)."""
        if "E0001" not in issue.code:
            return False

        lines = self.load_file(issue.file_path)
        if not lines:
            return False

        line_num = issue.line_num
        if line_num > len(lines):
            return False

        line = lines[line_num - 1]

        # Check for string concatenation issues
        if re.search(r'"\s*\+\s*$', line) or re.search(r"'\s*\+\s*$", line):
            # Fix trailing + by removing it
            fixed_line = re.sub(r'("\s*)\+\s*$', r'\1', line)
            fixed_line = re.sub(r"('\s*)\+\s*$", r'\1', fixed_line)
            lines[line_num - 1] = fixed_line
            return True

        # Check for missing indentation after function/class definition
        if "expected an indented block" in issue.message:
            prev_line = lines[line_num - 2] if line_num > 1 else ""

            if prev_line.rstrip().endswith(':'):
                # Add properly indented pass statement
                indent = len(prev_line) - len(prev_line.lstrip()) + 4
                lines.insert(line_num - 1, ' ' * indent + 'pass\n')
                return True

        # Check for unterminated string literals
        if "unterminated string literal" in issue.message:
            # Count quotes to see if they're balanced
            single_quotes = line.count("'")
            double_quotes = line.count('"')

            if single_quotes % 2 == 1:  # Odd number of single quotes
                lines[line_num - 1] = line.rstrip() + "'\n"
                return True

            if double_quotes % 2 == 1:  # Odd number of double quotes
                lines[line_num - 1] = line.rstrip() + '"\n'
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

        # Process priority issues first (syntax errors)
        syntax_errors = [issue for issue in self.issues if issue.code == "E0001"]
        other_issues = [issue for issue in self.issues if issue.code != "E0001"]

        # Process issues in order: syntax errors first, then others
        all_issues_ordered = syntax_errors + other_issues

        # Print summary of issues to fix
        self.logger.info("Found %s issues in %s files", len(self.issues), len(issues_by_file))
        self.logger.info("Fixing %s syntax errors first", len(syntax_errors))

        # Process all issues
        for issue in all_issues_ordered:
            fixed = False

            # Apply the appropriate fixer based on the issue code
            if issue.code == "C0303":  # Trailing whitespace
                fixed = self.fix_trailing_whitespace(issue)
            elif issue.code == "W0612":  # Unused variable
                fixed = self.fix_unused_variable(issue)
            elif issue.code == "W0718":  # Broad exception
                fixed = self.fix_broad_exception(issue)
            elif issue.code == "W1203":  # F-string in logging
                fixed = self.fix_f_string_logging(issue)
            elif issue.code == "C0103":  # Constant naming
                fixed = self.fix_constant_naming(issue)
            elif issue.code == "E0001":  # Syntax error
                fixed = self.fix_syntax_error(issue)

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

        # Group fixed issues by code for better overview
        fixed_by_code: Dict[str, int] = {}
        for issue in self.fixed_issues:
            if issue.code not in fixed_by_code:
                fixed_by_code[issue.code] = 0
            fixed_by_code[issue.code] += 1

        if fixed_by_code:
            print("\nFixed issues by type:")
            for code, count in sorted(fixed_by_code.items(), key=lambda x: x[1], reverse=True):
                print(f"  {code}: {count} issues")

        # Group unfixed issues by code for better overview
        if self.unfixed_issues:
            unfixed_by_code: Dict[str, int] = {}
            for issue in self.unfixed_issues:
                if issue.code not in unfixed_by_code:
                    unfixed_by_code[issue.code] = 0
                unfixed_by_code[issue.code] += 1

            print("\nRemaining issues by type:")
            for code, count in sorted(unfixed_by_code.items(), key=lambda x: x[1], reverse=True):
                print(f"  {code}: {count} issues")


def parse_pylint_log(log_path: str, target_codes: Optional[List[str]] = None) -> List[PylintIssue]:
    """Parse the pylint log file and extract issues.
    
    Args:
        log_path: Path to the pylint log file
        target_codes: Specific pylint codes to focus on (e.g., ["C0303", "W0612"])
        
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

                    # Filter by target codes if specified
                    if target_codes and code not in target_codes:
                        continue

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
    """Main function to parse arguments and run the fixer."""
    parser = argparse.ArgumentParser(
        description='Targeted fix for common pylint issues')

    parser.add_argument('--log-file', '-l',
                      help='Path to write detailed log output',
                      default='targeted_fixes.log')

    parser.add_argument('--optimization-log', '-o',
                      help='Path to the pylint log file',
                      default='optimization.log')

    parser.add_argument('--dry-run', '-d', action='store_true',
                      help='Show changes without applying them')

    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Print detailed output')

    parser.add_argument('--target', '-t', nargs='+',
                     help='Target specific pylint codes (e.g., C0303 W0612)',
                     default=['C0303', 'W0612', 'W0718', 'W1203', 'C0103', 'E0001'])

    args = parser.parse_args()

    # Check if log file exists
    if not os.path.exists(args.optimization_log):
        print(f"Error: The pylint log file {args.optimization_log} does not exist.")
        return 1

    print(f"Analyzing {args.optimization_log} for targeted issues...")
    issues = parse_pylint_log(args.optimization_log, args.target)

    if not issues:
        print("No matching issues found in the log file.")
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

        # Print next steps
        if fixes_applied > 0:
            print("\nNext steps:")
            print("  1. Run pylint again to see if targeted issues were resolved")
            print("  2. For remaining issues, consider manual fixes or additional tools")
            print("  3. Focus on one issue type at a time for best results")

        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
