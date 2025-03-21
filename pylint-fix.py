#!/usr/bin/env python3
"""
AILinux Code Optimization Tool

This script analyzes and fixes common lint issues in AILinux Python code.
It focuses on:
1. Fixing import statements
2. Improving exception handling
3. Refactoring redundant code
4. Addressing environment issues
"""
import os
import re
import sys
import argparse
import logging
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("AILinuxOptimizer")

class PythonFileFixer:
    """Fixes common lint issues in Python files."""
    
    def __init__(self, filepath: str, backup: bool = True):
        """
        Initialize the fixer.
        
        Args:
            filepath: Path to the Python file to fix
            backup: Whether to create a backup of the original file
        """
        self.filepath = filepath
        self.backup = backup
        self.content = ""
        self.original_content = ""
        self.fixes_applied = []
    
    def load_file(self) -> bool:
        """
        Load the file content.
        
        Returns:
            bool: True if file loaded successfully, False otherwise
        """
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.content = f.read()
                self.original_content = self.content
            return True
        except Exception as e:
            logger.error(f"Error loading {self.filepath}: {str(e)}")
            return False
    
    def save_file(self) -> bool:
        """
        Save the modified content back to the file.
        
        Returns:
            bool: True if file saved successfully, False otherwise
        """
        if self.content == self.original_content:
            logger.info(f"No changes made to {self.filepath}")
            return True
        
        try:
            # Create backup if requested
            if self.backup:
                backup_path = f"{self.filepath}.bak"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(self.original_content)
                logger.info(f"Created backup at {backup_path}")
            
            # Write changes
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(self.content)
            
            logger.info(f"Updated {self.filepath} with {len(self.fixes_applied)} fixes")
            for fix in self.fixes_applied:
                logger.info(f"  - {fix}")
            
            return True
        except Exception as e:
            logger.error(f"Error saving {self.filepath}: {str(e)}")
            return False
    
    def fix_imports(self) -> None:
        """Fix # Potential unused import: import statements and unused imports."""
        import_pattern = r'import\s+([^\n;]+)'
        from_import_pattern = r'from\s+([^\s]+)\s+import\s+([^\n;]+)'
        
        # Find all imports
        imports = re.findall(import_pattern, self.content)
        from_imports = re.findall(from_import_pattern, self.content)
        
        # Check for unused imports (this is a simple check and might have false positives)
        for imp in imports:
            module = imp.strip()
            if module.count(',') == 0:  # Simple module import
                if self.content.count(module) <= 1:  # Only in import statement
                    # Comment out potentially unused import
                    old_import = f"import {module}"
                    new_# Potential unused import: import = f"# Potential unused import: {old_import}"
                    if self.content.count(old_import) == 1:  # Avoid false replacements
                        self.content = self.content.replace(old_import, new_import)
                        self.fixes_applied.append(f"Commented potential unused import: {module}")
        
        # Organize imports (group standard library, third-party, and local imports)
        # This would require a more complex analysis, omitted for simplicity
    
    def fix_exception_handling(self) -> None:
        """Improve exception handling patterns."""
        # Find generic exception handlers
        generic_except_pattern = r'except\s+Exception\s+as\s+\w+:'
        generic_excepts = re.findall(generic_except_pattern, self.content)
        
        if generic_excepts:
            self.fixes_applied.append(f"Found {len(generic_excepts)} generic exception handlers that could be more specific")
        
        # Find and fix bare except blocks
        bare_except_pattern = r'except\s*:'
        bare_excepts = re.findall(bare_except_pattern, self.content)
        
        # Replace bare excepts with Exception
        if bare_excepts:
            self.content = re.sub(bare_except_pattern, 'except Exception:', self.content)
            self.fixes_applied.append(f"Replaced {len(bare_excepts)} bare 'except Exception:' with 'except Exception:'")
    
    def fix_f_strings(self) -> None:
        """Fix unnecessary f-strings."""
        # Find f-strings that don't contain any variables
        f_string_pattern = r'f["\']([^{}"\']*)["\']'
        unnecessary_f_strings = re.findall(f_string_pattern, self.content)
        
        count = 0
        for match in unnecessary_f_strings:
            old_str = f'f"{match}"'
            new_str = f'"{match}"'
            if old_str in self.content:
                self.content = self.content.replace(old_str, new_str)
                count += 1
            
            old_str = f"f'{match}'"
            new_str = f"'{match}'"
            if old_str in self.content:
                self.content = self.content.replace(old_str, new_str)
                count += 1
        
        if count > 0:
            self.fixes_applied.append(f"Removed {count} unnecessary f-strings")
    
    def fix_string_concatenation(self) -> None:
        """Fix string concatenation using + to use f-strings."""
        # Find string concatenation with variables
        concat_pattern = r'["\']\s*\+\s*(\w+)\s*\+\s*["\']'
        concats = re.findall(concat_pattern, self.content)
        
        # Count replacements (actual replacement would be complex)
        if concats:
            self.fixes_applied.append(f"Found {len(concats)} instances of string concatenation that could use f-strings")
    
    def fix_hardcoded_values(self) -> None:
        """Identify hardcoded values that should be constants or configs."""
        # Look for URLs, IP addresses, and port numbers
        url_pattern = r'["\'](https?://[^\s"\']+)["\']'
        ip_pattern = r'["\'](\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})["\']'
        port_pattern = r'["\'](\d{2,5})["\'].*port'
        
        urls = re.findall(url_pattern, self.content, re.IGNORECASE)
        ips = re.findall(ip_pattern, self.content)
        ports = re.findall(port_pattern, self.content, re.IGNORECASE)
        
        if urls or ips or ports:
            self.fixes_applied.append(f"Found hardcoded values: {len(urls)} URLs, {len(ips)} IPs, {len(ports)} ports")
    
    def fix_inconsistent_returns(self) -> None:
        """Fix inconsistent return patterns in functions."""
        # Find function definitions
        func_pattern = r'def\s+(\w+)\s*\([^)]*\)\s*(?:->\s*([^:]+)\s*)?:'
        functions = re.findall(func_pattern, self.content)
        
        for func_name, return_type in functions:
            # Find the function body (this is simplified)
            func_pattern = rf'def\s+{func_name}\s*\([^)]*\)[^:]*:(.*?)(?=\n\S|\Z)'
            func_matches = re.findall(func_pattern, self.content, re.DOTALL)
            
            if func_matches:
                func_body = func_matches[0]
                # Check for return statements
                returns = re.findall(r'return\s+([^;#\n]+)', func_body)
                
                # Check if function has return type but no return statement
                if return_type and return_type.strip() != 'None' and not returns:
                    self.fixes_applied.append(f"Function '{func_name}' has return type {return_type} but no return statement")
    
    def apply_all_fixes(self) -> None:
        """Apply all fixes to the file."""
        self.fix_imports()
        self.fix_exception_handling()
        self.fix_f_strings()
        self.fix_string_concatenation()
        self.fix_hardcoded_values()
        self.fix_inconsistent_returns()
    
    def fix_file(self) -> bool:
        """
        Load, fix, and save the file.
        
        Returns:
            bool: True if all operations were successful, False otherwise
        """
        if not self.load_file():
            return False
        
        self.apply_all_fixes()
        return self.save_file()


def scan_directory(directory: str, backup: bool = True) -> Dict[str, List[str]]:
    """
    Scan a directory for Python files and apply fixes.
    
    Args:
        directory: Directory to scan
        backup: Whether to create backups of modified files
    
    Returns:
        Dictionary mapping filenames to lists of applied fixes
    """
    results = {}
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                logger.info(f"Analyzing {filepath}")
                
                fixer = PythonFileFixer(filepath, backup)
                if fixer.fix_file():
                    results[filepath] = fixer.fixes_applied
    
    return results


def fix_start_js(js_path: str) -> bool:
    """
    Fix the incomplete start.js file.
    
    Args:
        js_path: Path to the start.js file
    
    Returns:
        bool: True if the file was fixed, False otherwise
    """
    try:
        # First create a backup
        backup_path = f"{js_path}.bak"
        try:
            with open(js_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            logger.info(f"Created backup of start.js at {backup_path}")
        except Exception as e:
            logger.error(f"Error creating backup of start.js: {str(e)}")
            return False
        
        # Check for incomplete const declaration at the end
        with open(js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if content.strip().endswith('const'):
            # Complete the file with a minimal valid syntax
            fixed_content = content + " configPath = path.join(__dirname, 'config.json');\n\n// End of file\n"
            
            with open(js_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            logger.info("Fixed incomplete start.js file")
            return True
        else:
            logger.info("start.js doesn't end with 'const', might need manual inspection")
            return False
    
    except Exception as e:
        logger.error(f"Error fixing start.js: {str(e)}")
        return False


def create_virtualenv(project_root: str) -> bool:
    """
    Create a Python virtual environment for the project.
    
    Args:
        project_root: Root directory of the project
    
    Returns:
        bool: True if virtual environment was created successfully, False otherwise
    """
    try:
        venv_path = os.path.join(project_root, 'venv')
        
        # Check if virtual environment already exists
        if os.path.exists(venv_path):
            logger.info(f"Virtual environment already exists at {venv_path}")
            return True
        
        # Create virtual environment
        logger.info(f"Creating virtual environment at {venv_path}")
        import subprocess
        result = subprocess.run([sys.executable, '-m', 'venv', venv_path], 
                               capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error creating virtual environment: {result.stderr}")
            return False
        
        # Create activation script for convenience
        activate_script = os.path.join(project_root, 'activate.sh')
        with open(activate_script, 'w') as f:
            f.write("""#!/bin/bash
# Activate AILinux virtual environment
source {venv_path}/bin/activate
""")
        
        # Make script executable
        os.chmod(activate_script, 0o755)
        
        logger.info(f"Created virtual environment at {venv_path}")
        logger.info(f"Created activation script at {activate_script}")
        logger.info("To activate the environment, run: source activate.sh")
        
        return True
    
    except Exception as e:
        logger.error(f"Error creating virtual environment: {str(e)}")
        return False


def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description="AILinux Code Optimization Tool")
    parser.add_argument('--dir', '-d', type=str, default='.',
                       help='Directory to scan (default: current directory)')
    parser.add_argument('--no-backup', '-n', action='store_true',
                       help='Do not create backups of modified files')
    parser.add_argument('--fix-js', '-j', action='store_true',
                       help='Fix the incomplete start.js file')
    parser.add_argument('--create-venv', '-v', action='store_true',
                       help='Create a Python virtual environment')
    parser.add_argument('--all', '-a', action='store_true',
                       help='Apply all fixes')
    
    args = parser.parse_args()
    
    # Resolve directory path
    directory = os.path.abspath(args.dir)
    logger.info(f"Working directory: {directory}")
    
    # Apply all fixes if requested
    if args.all:
        args.fix_js = True
        args.create_venv = True
    
    # Fix Python files
    results = scan_directory(directory, not args.no_backup)
    logger.info(f"Analyzed {len(results)} Python files")
    
    # Report results
    files_with_fixes = [f for f, fixes in results.items() if fixes]
    logger.info(f"Applied fixes to {len(files_with_fixes)} files")
    
    # Fix start.js if requested
    if args.fix_js:
        js_path = os.path.join(directory, 'start.js')
        if os.path.exists(js_path):
            if fix_start_js(js_path):
                logger.info("Fixed start.js file")
            else:
                logger.warning("Unable to automatically fix start.js")
        else:
            logger.warning(f"start.js not found at {js_path}")
    
    # Create virtual environment if requested
    if args.create_venv:
        if create_virtualenv(directory):
            logger.info("Created Python virtual environment")
            
            # Check if requirements.txt exists and suggest installation
            req_path = os.path.join(directory, 'requirements.txt')
            if os.path.exists(req_path):
                venv_python = os.path.join(directory, 'venv', 'bin', 'python')
                logger.info("To install requirements, run:")
                logger.info(f"{venv_python} -m pip install -r {req_path}")
        else:
            logger.warning("Failed to create Python virtual environment")
    
    logger.info("Optimization completed")


if __name__ == "__main__":
    main()
