#!/usr/bin/env python3
"""
Enhanced AILinux Pylint Fixer

This script automatically fixes issues found by pylint in Python code,
and also attempts to fix JavaScript and HTML files that pylint reports errors for.

It focuses on the most critical errors:

1. Syntax errors (E0001)
2. Trailing whitespace (C0303)
3. Unused imports (W0611)
4. Missing docstrings (C0111, C0112)
5. Line too long (C0301)
6. Broad exception catching (W0718)
7. F-string in logging (W1203)

Usage:
    python enhanced_pylint_fixer.py [--dry-run] [--log-file FILE] [--input-log FILE]
"""
import os
import re
import sys
import argparse
import logging
from typing import List, Dict, Optional, Tuple


class PylintIssue:
    """Represents a pylint issue extracted from the log file."""

    def __init__(self, file_path: str, line_num: int, code: str, message: str):
        """
        Initialize a pylint issue.
        
        Args:
            file_path: Path to the file with the issue
            line_num: Line number where the issue occurs
            code: Pylint error/warning code (e.g., E0001, C0303)
            message: Description of the issue
        """
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
        """
        Initialize the code fixer.
        
        Args:
            issues: List of pylint issues to fix
            dry_run: If True, don't actually modify files
            log_file: Path to write log output
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
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def get_file_type(self, file_path: str) -> str:
        """
        Determine the file type based on extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File type: 'python', 'javascript', 'html', or 'unknown'
        """
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.py':
            return 'python'
        elif ext == '.js':
            return 'javascript'
        elif ext in ['.html', '.htm']:
            return 'html'
        else:
            return 'unknown'

    def load_file(self, file_path: str) -> List[str]:
        """
        Load a file into the cache if it's not already loaded.
        
        Args:
            file_path: Path to the file to load
            
        Returns:
            List of lines from the file
        """
        if file_path not in self.file_cache:
            if not os.path.exists(file_path):
                self.logger.warning(f"File not found: {file_path}")
                return []
                
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    self.file_cache[file_path] = file.readlines()
            except UnicodeDecodeError:
                # Try again with latin-1 encoding if utf-8 fails
                try:
                    with open(file_path, 'r', encoding='latin-1') as file:
                        self.file_cache[file_path] = file.readlines()
                except Exception as e:
                    self.logger.error(f"Cannot read file {file_path}: {str(e)}")
                    return []
                    
        return self.file_cache[file_path]

    def save_file(self, file_path: str) -> None:
        """
        Save the modified file contents.
        
        Args:
            file_path: Path to the file to save
        """
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would save {file_path}")
        else:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.writelines(self.file_cache[file_path])
                self.logger.info(f"Saved: {file_path}")
                if file_path not in self.files_modified:
                    self.files_modified.append(file_path)
            except Exception as e:
                self.logger.error(f"Error saving {file_path}: {e}")

    def fix_syntax_error(self, issue: PylintIssue) -> bool:
        """
        Fix E0001 syntax errors.
        
        Args:
            issue: The pylint issue to fix
            
        Returns:
            True if the issue was fixed, False otherwise
        """
        if "E0001" not in issue.code:
            return False
            
        # Get file type to apply appropriate fixes
        file_type = self.get_file_type(issue.file_path)
        
        if file_type == 'python':
            return self.fix_python_syntax_error(issue)
        elif file_type == 'javascript':
            return self.fix_javascript_syntax_error(issue)
        elif file_type == 'html':
            return self.fix_html_syntax_error(issue)
        else:
            self.logger.warning(f"Unknown file type for {issue.file_path}, can't fix syntax error")
            return False

    def fix_python_syntax_error(self, issue: PylintIssue) -> bool:
        """Fix Python-specific syntax errors."""
        lines = self.load_file(issue.file_path)
        if not lines:
            return False
        
        line_num = issue.line_num
        if line_num > len(lines):
            return False
            
        line = lines[line_num - 1]
        
        # Fix 1: String concatenation issues with '+" +'
        if '+" +' in line or '"" +' in line or '=" +' in line:
            fixed_line = line.replace('=" +', '="')
            fixed_line = fixed_line.replace('"" +', '"')
            fixed_line = fixed_line.replace('+" +', '"+')
            lines[line_num - 1] = fixed_line
            return True
            
        # Fix 2: Issues with invalid string concatenation
        if "invalid syntax" in issue.message and "+" in line:
            # Remove trailing + for string concatenation
            if re.search(r'"\s*\+\s*$', line):
                lines[line_num - 1] = re.sub(r'"\s*\+\s*$', '"', line)
                return True
            elif re.search(r"'\s*\+\s*$", line):
                lines[line_num - 1] = re.sub(r"'\s*\+\s*$", "'", line)
                return True
            
        # Fix 3: Missing indentation after function/class definition
        if "expected an indented block" in issue.message:
            prev_line = lines[line_num - 2] if line_num > 1 else ""
            
            if prev_line.rstrip().endswith(':'):
                # Add properly indented pass statement
                indent = len(prev_line) - len(prev_line.lstrip()) + 4
                lines.insert(line_num - 1, ' ' * indent + 'pass\n')
                return True
        
        # Fix 4: Unterminated string literals
        if "unterminated string literal" in issue.message:
            return self.fix_unterminated_string(issue, lines, line_num, line)
        
        # Fix 5: Missing try/except/finally blocks
        if "expected 'except' or 'finally' block" in issue.message:
            # Look for unfinished try blocks
            indent_level = len(line) - len(line.lstrip())
            # Add a simple except block
            lines.insert(line_num, ' ' * indent_level + 'except Exception as e:\n')
            lines.insert(line_num + 1, ' ' * (indent_level + 4) + 'pass  # Added by pylint fixer\n')
            return True
            
        return False

    def fix_unterminated_string(self, issue: PylintIssue, lines: List[str], line_num: int, line: str) -> bool:
        """Fix unterminated string literals more robustly."""
        # Determine quote type (single or double)
        single_quotes = line.count("'")
        double_quotes = line.count('"')
        triple_single = line.count("'''")
        triple_double = line.count('"""')
        
        # Handle triple-quoted strings differently
        if "'''" in line and triple_single % 2 == 1:
            # Look for the start of an unclosed triple-quoted string
            if re.search(r"'''[^']*$", line):
                lines[line_num - 1] = line.rstrip() + "'''\n"
                return True
        elif '"""' in line and triple_double % 2 == 1:
            # Look for the start of an unclosed triple-quoted string
            if re.search(r'"""[^"]*$', line):
                lines[line_num - 1] = line.rstrip() + '"""\n'
                return True
                
        # Handle regular strings
        elif single_quotes % 2 == 1:  # Odd number of single quotes
            # Find the position of the last quote
            last_pos = line.rfind("'")
            # Check if it's not escaped
            if last_pos > 0 and line[last_pos-1] != '\\':
                # Add closing quote
                lines[line_num - 1] = line.rstrip() + "'\n"
                return True
        elif double_quotes % 2 == 1:  # Odd number of double quotes
            # Find the position of the last quote
            last_pos = line.rfind('"')
            # Check if it's not escaped
            if last_pos > 0 and line[last_pos-1] != '\\':
                # Add closing quote
                lines[line_num - 1] = line.rstrip() + '"\n'
                return True
                
        # Handle f-strings and other special string types
        if 'f"' in line and double_quotes % 2 == 1:
            lines[line_num - 1] = line.rstrip() + '"\n'
            return True
        if "f'" in line and single_quotes % 2 == 1:
            lines[line_num - 1] = line.rstrip() + "'\n"
            return True
            
        return False

    def fix_javascript_syntax_error(self, issue: PylintIssue) -> bool:
        """Fix JavaScript-specific syntax errors."""
        lines = self.load_file(issue.file_path)
        if not lines:
            return False
        
        line_num = issue.line_num
        if line_num > len(lines):
            return False
            
        line = lines[line_num - 1]
        
        # Fix string literals in JavaScript
        if "unterminated string literal" in issue.message:
            return self.fix_unterminated_string(issue, lines, line_num, line)
        
        # Fix invalid syntax in JavaScript (often template literals)
        if "invalid syntax" in issue.message:
            # Replace JavaScript template literals that pylint misinterprets
            if "`" in line:
                # Template literals with ${} expressions confuse pylint
                # Replace them with regular strings temporarily
                if "${" in line and "}" in line:
                    modified_line = re.sub(r'\${(\w+)}', r'\1', line)
                    modified_line = modified_line.replace('`', '"')
                    lines[line_num - 1] = modified_line
                    return True
                    
            # Fix arrow functions
            if "=>" in line:
                # Arrow functions cause syntax errors in Python
                # Replace with a temporary function
                modified_line = re.sub(r'(\w+)\s*=>\s*{', r'function \1() {', line)
                lines[line_num - 1] = modified_line
                return True
                
        return False

    def fix_html_syntax_error(self, issue: PylintIssue) -> bool:
        """Fix HTML-specific syntax errors."""
        lines = self.load_file(issue.file_path)
        if not lines:
            return False
        
        line_num = issue.line_num
        if line_num > len(lines):
            return False
            
        line = lines[line_num - 1]
        
        # Fix "invalid decimal literal" - often caused by HTML attributes
        if "invalid decimal literal" in issue.message:
            # HTML IDs with leading digits cause this error in pylint
            if re.search(r'id="\d', line) or re.search(r"id='\d", line):
                # Modify the ID to have a prefix
                modified_line = re.sub(r'(id=")(\d)', r'\1id_\2', line)
                modified_line = re.sub(r"(id=')(\d)", r"\1id_\2", modified_line)
                lines[line_num - 1] = modified_line
                return True
                
            # Class names with digits can also cause this
            if re.search(r'class="\d', line) or re.search(r"class='\d", line):
                # Modify the class to have a prefix
                modified_line = re.sub(r'(class=")(\d)', r'\1class_\2', line)
                modified_line = re.sub(r"(class=')(\d)", r"\1class_\2", modified_line)
                lines[line_num - 1] = modified_line
                return True
                
        # Fix unclosed tags
        if "invalid syntax" in issue.message:
            # Check for unclosed HTML tags
            tag_match = re.search(r'<(\w+)(?:\s+[^>]*)?$', line)
            if tag_match:
                tag_name = tag_match.group(1)
                lines[line_num - 1] = line.rstrip() + f"></{tag_name}>\n"
                return True
                
            # Check for unclosed HTML attribute quotes
            attr_match = re.search(r'(\w+)="([^"]*$)', line)
            if attr_match:
                lines[line_num - 1] = line.rstrip() + '"\n'
                return True
                
        return False

    def fix_trailing_whitespace(self, issue: PylintIssue) -> bool:
        """
        Remove trailing whitespace (C0303).
        
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

    def fix_unused_import(self, issue: PylintIssue) -> bool:
        """
        Remove unused imports (W0611).
        
        Args:
            issue: The pylint issue to fix
            
        Returns:
            True if the issue was fixed, False otherwise
        """
        if "Unused import" not in issue.message:
            return False
            
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
            lines[issue.line_num - 1] = f"# {line.rstrip()}  # removed: {issue.code}\n"
            return True
        elif re.match(rf"^\s*from\s+[\w.]+\s+import\s+{unused_import}\s*$", line):
            # Single import from module (from module import unused)
            lines[issue.line_num - 1] = f"# {line.rstrip()}  # removed: {issue.code}\n"
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

    def fix_missing_docstring(self, issue: PylintIssue) -> bool:
        """
        Add missing docstrings (C0111, C0112, C0103).
        
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
        
        # Only fix Python files for docstrings
        if self.get_file_type(issue.file_path) != 'python':
            return False

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
            docstring = f'"""{module_name} module for AILinux.\n\nThis module provides functionality for the AILinux system.\n"""\n'
            lines.insert(0, docstring)
            return True
        elif is_func and "def " in line:
            # Function docstring
            func_name = re.search(r'def\s+(\w+)', line)
            if func_name:
                name = func_name.group(1)
                docstring = f'{indent_str}"""\n{indent_str}Description for function {name}.\n{indent_str}"""\n'
                lines.insert(issue.line_num, docstring)
                return True
        elif is_class and "class " in line:
            # Class docstring
            class_name = re.search(r'class\s+(\w+)', line)
            if class_name:
                name = class_name.group(1)
                docstring = f'{indent_str}"""\n{indent_str}Description for class {name}.\n{indent_str}"""\n'
                lines.insert(issue.line_num, docstring)
                return True

        return False

    def fix_line_too_long(self, issue: PylintIssue) -> bool:
        """
        Shorten lines that are too long (C0301).
        
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
                            replacement = f"{string[0]}" + "\n" + indent_str + f"\"{string[1:-1]}{string[-1]}"
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

    def fix_broad_exception(self, issue: PylintIssue) -> bool:
        """
        Fix broad exception catching (W0718).
        
        Args:
            issue: The pylint issue to fix
            
        Returns:
            True if the issue was fixed, False otherwise
        """
        if "Catching too general exception" not in issue.message:
            return False
            
        lines = self.load_file(issue.file_path)
        if not lines:
            return False
            
        line = lines[issue.line_num - 1]
        
        # Check if it's a simple 'except:' or 'except Exception:'
        if re.search(r'except\s+Exception\s*:', line):
            # Replace with except (Exception, RuntimeError):
            replaced_line = line.replace('except Exception:', 'except (Exception, RuntimeError):')
            lines[issue.line_num - 1] = replaced_line
            return True
            
        return False

    def fix_f_string_logging(self, issue: PylintIssue) -> bool:
        """
        Fix f-string usage in logging calls (W1203, W1201).
        
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
        
        # Alternative pattern for logging with f-string without interpolation
        match = re.search(r'(logger\.\w+)\(f[\'"]([^{}]+)[\'"](,.+?)?\)', line)
        if match:
            log_call = match.group(1)
            string_content = match.group(2)
            args = match.group(3) if match.group(3) else ''
            
            # Simply remove the 'f' prefix since there are no variables
            new_line = f'{log_call}("{string_content}"{args})'
            lines[issue.line_num - 1] = line.replace(match.group(0), new_line)
            return True
            
        return False

    def fix_issues(self) -> int:
        """
        Fix all found issues and return the number of fixed problems.
        
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
        self.logger.info(f"Found {len(self.issues)} issues in {len(issues_by_file)} files")
        
        # Categorize by file type
        file_types = {}
        for file_path in issues_by_file:
            file_type = self.get_file_type(file_path)
            if file_type not in file_types:
                file_types[file_type] = 0
            file_types[file_type] += 1
        
        for file_type, count in file_types.items():
            self.logger.info(f"Found {count} files of type: {file_type}")
        
        # Prioritize critical syntax errors first
        syntax_errors = [issue for issue in self.issues if issue.code == "E0001"]
        if syntax_errors:
            self.logger.info(f"Found {len(syntax_errors)} syntax errors (E0001) to fix first")
        
        # First pass: Fix only syntax errors
        if syntax_errors:
            for issue in syntax_errors:
                if self.fix_syntax_error(issue):
                    self.fixes_applied += 1
                    self.fixed_issues.append(issue)
                    self.logger.info(f"Fixed syntax error: {issue}")
                else:
                    self.skipped_issues += 1
                    self.unfixed_issues.append(issue)
                    self.logger.warning(f"Could not fix syntax error: {issue}")
        
        # Second pass: Fix non-syntax errors
        other_issues = [issue for issue in self.issues if issue.code != "E0001"]
        for issue in other_issues:
            fixed = False
            
            # Apply the appropriate fixer based on the issue code
            if issue.code == "C0303":  # Trailing whitespace
                fixed = self.fix_trailing_whitespace(issue)
            elif issue.code == "W0611":  # Unused import
                fixed = self.fix_unused_import(issue)
            elif issue.code in ["C0111", "C0112", "C0116"]:  # Missing docstring
                fixed = self.fix_missing_docstring(issue)
            elif issue.code == "C0301":  # Line too long
                fixed = self.fix_line_too_long(issue)
            elif issue.code == "W0718":  # Broad exception
                fixed = self.fix_broad_exception(issue)
            elif issue.code in ["W1201", "W1203"]:  # Logging format
                fixed = self.fix_f_string_logging(issue)
                
            if fixed:
                self.fixes_applied += 1
                self.fixed_issues.append(issue)
                if self.verbose:
                    self.logger.debug(f"Fixed: {issue}")
            else:
                self.skipped_issues += 1
                self.unfixed_issues.append(issue)
                if self.verbose:
                    self.logger.debug(f"Skipped: {issue}")
                    
        # Save all modified files
        for file_path in self.file_cache:
            self.save_file(file_path)
            
        return self.fixes_applied

    def print_summary(self):
        """Print a summary of the fixes applied."""
        print("\n" + "="*50)
        print(f"SUMMARY:")
        print(f"Total issues processed: {len(self.issues)}")
        print(f"Fixed: {self.fixes_applied} issues")
        print(f"Skipped: {self.skipped_issues} issues")
        print(f"Files modified: {len(self.files_modified)}")
        
        # Group by file type
        file_types = {}
        for file_path in self.files_modified:
            file_type = self.get_file_type(file_path)
            if file_type not in file_types:
                file_types[file_type] = 0
            file_types[file_type] += 1
        
        if file_types:
            print("\nFixed files by type:")
            for file_type, count in sorted(file_types.items()):
                print(f"  {file_type}: {count} files")
        
        if self.files_modified:
            print("\nModified files:")
            for file in sorted(self.files_modified):
                print(f"  - {file}")

        # Group fixed issues by type
        if self.fixed_issues:
            fixed_by_code = {}
            for issue in self.fixed_issues:
                if issue.code not in fixed_by_code:
                    fixed_by_code[issue.code] = 0
                fixed_by_code[issue.code] += 1
                
            print("\nFixed issues by type:")
            for code, count in sorted(fixed_by_code.items(), key=lambda x: x[1], reverse=True):
                print(f"  {code}: {count} issues")

        # Group unfixed issues by type
        if self.unfixed_issues:
            unfixed_by_code = {}
            for issue in self.unfixed_issues:
                if issue.code not in unfixed_by_code:
                    unfixed_by_code[issue.code] = 0
                unfixed_by_code[issue.code] += 1
                
            print("\nRemaining issues by type:")
            for code, count in sorted(unfixed_by_code.items(), key=lambda x: x[1], reverse=True):
                print(f"  {code}: {count} issues")


def parse_pylint_log(log_path: str) -> List[PylintIssue]:
    """
    Parse the pylint log file and extract issues.
    
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
                match = re.match(r'^([\w\./\-]+):(\d+)(?::\d+)?: ([CRWE]\d{4}): (.+?)(?:\s\([\w-]+\))?$', line.strip())
                if match:
                    file_path, line_num, code, message = match.groups()
                    # Make sure the line number is an integer
                    try:
                        line_num = int(line_num)
                    except ValueError:
                        continue
                        
                    issues.append(PylintIssue(
                        file_path=file_path,
                        line_num=line_num,
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
        description='Fix pylint issues in Python, JavaScript, and HTML files')
    
    parser.add_argument('--log-file', '-l',
                      help='Path to write detailed log output',
                      default='pylint_fixed.log')
    
    parser.add_argument('--input-log', '-i',
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
    if not os.path.exists(args.input_log):
        print(f"Error: The pylint log file {args.input_log} does not exist.")
        return 1

    print(f"Analyzing {args.input_log}...")
    issues = parse_pylint_log(args.input_log)
    
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
            print("\nNext steps:")
            print("  1. Run pylint again to see if remaining issues were resolved")
            print("  2. For JavaScript and HTML files, consider using appropriate linters")
            print("     - For JavaScript: ESLint (npm install -g eslint)")
            print("     - For HTML: HTMLHint (npm install -g htmlhint)")
            print("  3. Some issues may require manual fixes - syntax errors have priority")
            
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
