#!/usr/bin/env python3
"""
AILinux Directory Structure Validator and Fixer

This module checks and restores the expected directory structure
for the AILinux project, and runs pylint to verify code quality.
"""
import os
import subprocess


def restore_directory_structure(base_dir):
    """
    Check and restore the expected directory structure.
    
    Args:
        base_dir: The base directory to check
    """
    expected_structure = {
        'backend': {
            'backend': ['ai_model.py', 'app.py', 'backend.js', 'package-lock.json'],
            'frontend': ['config.py', 'index.html', 'main.js', 'package.json'],
            'models': [],
            'lib': ['libggml-base.so', 'libggml-cpu-alderlake.so'],
        },
        'logs': ['backend.log', 'frontend.log'],
        'readme': ['README.md']
    }
    
    # Helper function to create the directory structure
    def create_structure(target_path, structure):
        """Create directories and files based on expected structure."""
        for key, value in structure.items():
            target_dir = os.path.join(target_path, key)
            if isinstance(value, list):
                os.makedirs(target_dir, exist_ok=True)
                for file in value:
                    file_path = os.path.join(target_dir, file)
                    if not os.path.exists(file_path):
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write('')
            elif isinstance(value, dict):
                os.makedirs(target_dir, exist_ok=True)
                create_structure(target_dir, value)
    
    # Create the directory structure
    create_structure(base_dir, expected_structure)
    print(f"Directory structure verified and restored in {base_dir}")


def run_pylint():
    """Run pylint with specific options to check the code."""
    try:
        result = subprocess.run(
            ['pylint', '--disable=all', '--enable=error'],
            capture_output=True, 
            text=True,
            check=True
        )
        print(result.stdout)
        if result.stderr:
            print("Error:", result.stderr)
    except FileNotFoundError:
        print("Pylint is not installed. Install it with 'pip install pylint'.")


if __name__ == "__main__":
    base_dir = '/home/zombie/ailinux'
    restore_directory_structure(base_dir)
    run_pylint()
