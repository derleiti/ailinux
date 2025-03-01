#!/usr/bin/env python3
"""
AILinux Code Optimization Bugfix Script

This script fixes common code issues identified by the pylint analysis in the optimization.log file.
It focuses on the most critical errors, including syntax errors, indentation issues, and docstring problems.
"""
import os
import re
import sys
import subprocess
from pathlib import Path

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_DIR = os.path.join(BASE_DIR, "client")


def fix_adjust_hierarchy_with_debugger():
    """Fix syntax errors in the adjust_hierarchy_with_debugger.py file."""
    filepath = os.path.join(CLIENT_DIR, "adjust_hierarchy_with_debugger.py")
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return False
    
    print(f"Fixing adjust_hierarchy_with_debugger.py...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix the unexpected indent issue on line 15
        lines = content.split('\n')
        
        # The error is on this line:
        # result = subprocess.run(check=True)(['pylint', '--disable=all', '--enable=error'],
        # Fix it by correcting the function call
        for i, line in enumerate(lines):
            if "result = subprocess.run(check=True)" in line:
                lines[i] = "result = subprocess.run(['pylint', '--disable=all', '--enable=error'], check=True,"
            if "capture_output=True, text=True)" in line:
                # Next line has the remaining arguments
                lines[i] = "                         capture_output=True, text=True)"
        
        # Add missing docstring for the module
        if not lines[0].startswith('"""'):
            lines.insert(0, '"""Tool to adjust directory hierarchy and run pylint checks."""')
        
        # Write the fixed content back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"✅ Fixed adjust_hierarchy_with_debugger.py")
        return True
    
    except Exception as e:
        print(f"Error fixing {filepath}: {str(e)}")
        return False


def fix_missing_docstrings():
    """Add missing docstrings to Python files."""
    python_files = []
    
    # Find all Python files in the client directory
    for root, _, files in os.walk(CLIENT_DIR):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    fixed_count = 0
    for filepath in python_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check if the file is missing a module docstring
            if not content.strip().startswith('"""'):
                filename = os.path.basename(filepath)
                print(f"Adding missing docstring to {filename}")
                
                # Generate a simple docstring based on the filename
                module_name = os.path.splitext(filename)[0]
                module_name = module_name.replace('_', ' ').title()
                docstring = f'"""{module_name} module for AILinux.\n\nThis module provides functionality for the AILinux system.\n"""\n'
                
                # Add the docstring to the beginning of the file
                content = docstring + content
                
                # Write the fixed content back
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                fixed_count += 1
        
        except Exception as e:
            print(f"Error adding docstring to {filepath}: {str(e)}")
    
    print(f"✅ Added missing docstrings to {fixed_count} Python files")
    return fixed_count > 0


def fix_file_sync_client():
    """Fix the file-sync-client.py errors."""
    filepath = os.path.join(CLIENT_DIR, "file-sync-client.py")
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return False
    
    print(f"Fixing file-sync-client.py...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix the missing import for 'stat' module
        if "import stat" not in content:
            # Add the stat import at the top with other imports
            modified_content = re.sub(
                r'import (.*?)from dotenv import load_dotenv',
                r'import \1import stat\nfrom dotenv import load_dotenv',
                content,
                flags=re.DOTALL
            )
            
            # Fix the possibly-used-before-assignment error with stat
            # by ensuring stat is imported before it's used
            
            # Remove trailing whitespace
            modified_content = '\n'.join(line.rstrip() for line in modified_content.split('\n'))
            
            # Write the fixed content back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            print(f"✅ Fixed file-sync-client.py")
            return True
    
    except Exception as e:
        print(f"Error fixing {filepath}: {str(e)}")
        return False


def fix_alphaos_py():
    """Fix the issues in alphaos.py."""
    filepath = os.path.join(CLIENT_DIR, "alphaos.py")
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return False
    
    print(f"Fixing alphaos.py...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix the method override issues by removing 'async' to match parent class expectations
        # or by using the correct method names
        modified_content = content.replace(
            "async def onConnect", 
            "def onConnect"
        ).replace(
            "async def onOpen", 
            "def onOpen"
        ).replace(
            "async def onMessage", 
            "def onMessage"
        ).replace(
            "async def onClose", 
            "def onClose"
        )
        
        # Add docstring if missing
        if not modified_content.strip().startswith('"""'):
            modified_content = '"""WebSocket client for AILinux using Autobahn.\n\nProvides connection to WebSocket server on derleiti.de.\n"""\n' + modified_content
        
        # Write the fixed content back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print(f"✅ Fixed alphaos.py")
        return True
    
    except Exception as e:
        print(f"Error fixing {filepath}: {str(e)}")
        return False


def fix_start_js():
    """Fix syntax issues in start.js."""
    filepath = os.path.join(CLIENT_DIR, "start.js")
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return False
    
    print(f"Fixing start.js...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix invalid syntax in the file
        # The main issue is with multi-line strings in JavaScript
        # Use template literals with backticks for multi-line strings
        if "logMessage(`Configuration: Flask=${flaskHost}:${flaskPort}, WebSocket=${wsServerUrl}`,\nstartLogPath)" in content:
            modified_content = content.replace(
                "logMessage(`Configuration: Flask=${flaskHost}:${flaskPort}, WebSocket=${wsServerUrl}`,\nstartLogPath)",
                "logMessage(`Configuration: Flask=${flaskHost}:${flaskPort}, WebSocket=${wsServerUrl}`, startLogPath)"
            )
        
            # Write the fixed content back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            print(f"✅ Fixed start.js")
            return True
    
    except Exception as e:
        print(f"Error fixing {filepath}: {str(e)}")
        return False


def fix_websocket_client_py():
    """Fix trailing whitespace in websocket_client.py."""
    filepath = os.path.join(CLIENT_DIR, "websocket_client.py")
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return False
    
    print(f"Fixing websocket_client.py...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix trailing whitespace
        modified_content = '\n'.join(line.rstrip() for line in content.split('\n'))
        
        # Add docstring if missing
        if not modified_content.strip().startswith('"""'):
            modified_content = '"""WebSocket client for connecting to AILinux server.\n\nProvides functionality to establish WebSocket connections and handle messages.\n"""\n' + modified_content
        
        # Write the fixed content back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print(f"✅ Fixed websocket_client.py")
        return True
    
    except Exception as e:
        print(f"Error fixing {filepath}: {str(e)}")
        return False


def fix_websocket_client_with_dash():
    """Fix the naming issue in websocket-client.py."""
    old_filepath = os.path.join(CLIENT_DIR, "websocket-client.py")
    new_filepath = os.path.join(CLIENT_DIR, "websocket_client_module.py")
    
    if not os.path.exists(old_filepath):
        print(f"File not found: {old_filepath}")
        return False
    
    print(f"Fixing websocket-client.py naming issue...")
    
    try:
        with open(old_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix trailing whitespace
        modified_content = '\n'.join(line.rstrip() for line in content.split('\n'))
        
        # Add docstring if missing
        if not modified_content.strip().startswith('"""'):
            modified_content = '"""WebSocket client module for AILinux.\n\nProvides connection functionality to AILinux WebSocket server.\n"""\n' + modified_content
        
        # Write to the new file with a proper snake_case name
        with open(new_filepath, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        # Optionally, remove the old file
        # os.remove(old_filepath)
        
        print(f"✅ Fixed websocket-client.py naming issue by creating websocket_client_module.py")
        return True
    
    except Exception as e:
        print(f"Error fixing {old_filepath}: {str(e)}")
        return False


def fix_config_py():
    """Fix the config.py file with the redefined built-in 'set'."""
    filepath = os.path.join(CLIENT_DIR, "frontend", "config.py")
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return False
    
    print(f"Fixing config.py...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Rename the 'set' function to avoid redefining the built-in
        modified_content = content.replace("def set(key, value):", "def set_config(key, value):")
        
        # Add docstring if missing
        if not modified_content.strip().startswith('"""'):
            modified_content = '"""Configuration module for AILinux frontend.\n\nProvides settings management for the application.\n"""\n' + modified_content
        
        # Write the fixed content back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print(f"✅ Fixed config.py")
        return True
    
    except Exception as e:
        print(f"Error fixing {filepath}: {str(e)}")
        return False


def run_pylint():
    """Run pylint on the codebase to check if the fixes resolved the issues."""
    print("Running pylint to check if issues are resolved...")
    
    try:
        # Run pylint only on Python files
        command = ["pylint"]
        
        # Find all Python files in the client directory
        python_files = []
        for root, _, files in os.walk(CLIENT_DIR):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        if not python_files:
            print("No Python files found to check with pylint")
            return False
        
        # Run pylint on a small subset for testing
        sample_files = python_files[:5]
        print(f"Running pylint on sample files: {', '.join(os.path.basename(f) for f in sample_files)}")
        
        result = subprocess.run(command + sample_files, capture_output=True, text=True)
        
        # Save the output to a new log file
        with open("optimization_fixed.log", "w") as log_file:
            log_file.write(result.stdout)
        
        if result.returncode == 0:
            print("✅ Pylint passed without errors!")
        else:
            print("⚠️ Pylint found some issues, but hopefully fewer than before.")
            print("  See optimization_fixed.log for details")
        
        return True
    
    except Exception as e:
        print(f"Error running pylint: {str(e)}")
        return False


def main():
    """Main function to run all fixes."""
    print("🔧 AILinux Code Optimization Bugfix Script 🔧")
    print("============================================")
    
    # Run all fixes
    fixes = [
        fix_adjust_hierarchy_with_debugger,
        fix_file_sync_client,
        fix_alphaos_py,
        fix_start_js,
        fix_websocket_client_py,
        fix_websocket_client_with_dash,
        fix_config_py,
        fix_missing_docstrings,
    ]
    
    success_count = 0
    for fix_function in fixes:
        if fix_function():
            success_count += 1
    
    print(f"\n✅ Applied {success_count}/{len(fixes)} fixes successfully!")
    
    # Run pylint to check if issues are resolved
    run_pylint()
    
    print("\n🎉 Fixes completed! The code should now have fewer issues.")
    print("   Re-run pylint on the entire codebase to verify all issues are resolved.")
    

if __name__ == "__main__":
    main()
