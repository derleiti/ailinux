#!/usr/bin/env python3
"""
Python Code Optimizer Script

This script optimizes Python code to fix common pylint issues and improve code quality.
It scans Python files in a directory tree and applies fixes for common issues like:
- Unused imports
- String formatting issues
- Empty pass statements
- Import ordering
- Docstring formatting

Usage:
    python optimize_python.py [directory]
"""

import os
import sys
import re
import glob
import subprocess
from typing import List, Dict, Tuple, Set, Optional, Any


def find_python_files(base_dir: str) -> List[str]:
    """Find all Python files in directory tree.
    
    Args:
        base_dir: Base directory to search
        
    Returns:
        List of Python file paths
    """
    return glob.glob(f"{base_dir}/**/*.py", recursive=True)


def run_pylint(file_path: str) -> Tuple[str, str]:
    """Run pylint on a specific file and return result.
    
    Args:
        file_path: Path to Python file
        
    Returns:
        Tuple of (stdout, stderr) from pylint
    """
    try:
        command = ["pylint", "--output-format=json", file_path]
        result = subprocess.run(command, capture_output=True, text=True)
        return result.stdout, result.stderr
    except FileNotFoundError:
        print("Pylint not found. Install it with 'pip install pylint'")
        return "", "Pylint not found"


def fix_unused_imports(content: str) -> Tuple[str, bool]:
    """Fix unused imports marked with W0611.
    
    Args:
        content: File content
        
    Returns:
        Tuple of (modified content, was modified)
    """
    # Pattern to match import lines that are commented out with W0611
    pattern = r'^\s*#\s*import\s+.*?(\s*#\s*.*?W0611.*)$'
    pattern2 = r'^\s*#\s*from\s+.*?(\s*#\s*.*?W0611.*)$'
    
    # Also match import lines with W0611 at the end
    import_pattern = r'^(\s*import\s+.*?)(\s*#\s*.*?W0611.*)$'
    from_pattern = r'^(\s*from\s+.*?)(\s*#\s*.*?W0611.*)$'
    
    modified = False
    
    # Remove fully commented imports
    new_content = re.sub(pattern, '', content, flags=re.MULTILINE)
    if new_content != content:
        modified = True
        content = new_content
    
    # Remove fully commented from imports
    new_content = re.sub(pattern2, '', content, flags=re.MULTILINE)
    if new_content != content:
        modified = True
        content = new_content
    
    # Remove imports with W0611 comment
    new_content = re.sub(import_pattern, '', content, flags=re.MULTILINE)
    if new_content != content:
        modified = True
        content = new_content
    
    # Remove from imports with W0611 comment
    new_content = re.sub(from_pattern, '', content, flags=re.MULTILINE)
    if new_content != content:
        modified = True
        content = new_content
    
    return content, modified


def fix_string_formatting(content: str) -> Tuple[str, bool]:
    """Fix string formatting issues (convert %s to f-strings).
    
    Args:
        content: File content
        
    Returns:
        Tuple of (modified content, was modified)
    """
    modified = False
    
    # Find logger statements with %s formatting
    patterns = [
        # Logger statements with %s
        (r'logger\.(debug|info|warning|error|critical)\((["\']).*?%s.*?\2,\s*(.*?)\)', 
         lambda m: f'logger.{m.group(1)}(f{m.group(2)}{m.group(0)[m.group(0).find("(")+2:m.group(0).find("%s")]}{{{"{"}{m.group(3)}{"}"}"{m.group(0)[m.group(0).find("%s")+2:m.group(0).rfind(",")]}"){m.group(2)})"'),
        
        # String concatenation with "f"" + " patterns
        (r'f(["\'])\s*\+\s*\n\s*(["\'])', r'f\1\n    \2'),
        
        # Print statements with %s
        (r'print\((["\']).*?%s.*?\1,\s*(.*?)\)', 
         lambda m: f'print(f{m.group(1)}{m.group(0)[m.group(0).find("(")+2:m.group(0).find("%s")]}{{{"{"}{m.group(2)}{"}"}"{m.group(0)[m.group(0).find("%s")+2:m.group(0).rfind(",")]}"{m.group(1)})")'),
    ]
    
    for pattern, replacement in patterns:
        if callable(replacement):
            # For complex replacements that need a function
            matches = list(re.finditer(pattern, content, re.MULTILINE))
            if matches:
                modified = True
                # Start from the end to avoid messing up positions
                for match in reversed(matches):
                    start, end = match.span()
                    replacement_text = replacement(match)
                    content = content[:start] + replacement_text + content[end:]
        else:
            # For simple string replacements
            new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            if new_content != content:
                modified = True
                content = new_content
    
    return content, modified


def fix_redundant_pass(content: str) -> Tuple[str, bool]:
    """Fix redundant pass statements.
    
    Args:
        content: File content
        
    Returns:
        Tuple of (modified content, was modified)
    """
    modified = False
    
    # Pattern to match multiple consecutive pass statements
    pattern = r'(\s+pass\s*\n)(\s+pass\s*\n)+'
    new_content = re.sub(pattern, r'\1', content)
    if new_content != content:
        modified = True
        content = new_content
    
    # Also fix large blocks of pass statements (more than 5)
    pattern = r'(\s+pass\s*\n)(\s+pass\s*\n){4,}'
    new_content = re.sub(pattern, r'\1', content)
    if new_content != content:
        modified = True
    
    return new_content, modified


def fix_docstring_formatting(content: str) -> Tuple[str, bool]:
    """Fix docstring formatting issues.
    
    Args:
        content: File content
        
    Returns:
        Tuple of (modified content, was modified)
    """
    modified = False
    
    # Pattern to match empty docstrings
    pattern = r'""""\s*"""'
    new_content = re.sub(pattern, '"""Docstring placeholder."""', content)
    if new_content != content:
        modified = True
        content = new_content
    
    # Pattern to match docstrings with just "Beschreibung"
    pattern = r'"""\s*Beschreibung für.*?\."""'
    new_content = re.sub(pattern, 
                         lambda m: m.group(0).replace('Beschreibung für', 'Description for'), 
                         content)
    if new_content != content:
        modified = True
        content = new_content
    
    return content, modified


def optimize_file(file_path: str) -> List[str]:
    """Optimize a Python file by fixing common issues.
    
    Args:
        file_path: Path to Python file
        
    Returns:
        List of fixes applied
    """
    fixes = []
    
    try:
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        original_content = content
        
        # Apply fixes
        content, modified1 = fix_unused_imports(content)
        if modified1:
            fixes.append("Removed unused imports")
        
        content, modified2 = fix_string_formatting(content)
        if modified2:
            fixes.append("Fixed string formatting")
        
        content, modified3 = fix_redundant_pass(content)
        if modified3:
            fixes.append("Removed redundant pass statements")
        
        content, modified4 = fix_docstring_formatting(content)
        if modified4:
            fixes.append("Fixed docstring formatting")
        
        # Write back if any changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return []
    
    return fixes


def optimize_all_files(base_dir: str) -> Dict[str, List[str]]:
    """Run optimization on all Python files.
    
    Args:
        base_dir: Base directory to search
        
    Returns:
        Dictionary mapping file paths to lists of fixes applied
    """
    python_files = find_python_files(base_dir)
    results = {}
    
    for file_path in python_files:
        print(f"Optimizing {file_path}...")
        fixes = optimize_file(file_path)
        if fixes:
            results[file_path] = fixes
    
    return results


def main():
    """Main function."""
    base_dir = "."
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    
    print(f"Optimizing Python files in {os.path.abspath(base_dir)}")
    results = optimize_all_files(base_dir)
    
    if results:
        print("\nOptimization Results:")
        for file_path, fixes in results.items():
            print(f"\n{file_path}:")
            for fix in fixes:
                print(f"  - {fix}")
        
        print(f"\nTotal files optimized: {len(results)}")
    else:
        print("\nNo fixes applied.")


if __name__ == "__main__":
    main()
