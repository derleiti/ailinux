"""
Module Path Fixer for AILinux Backend

This module ensures that all imports in the AILinux backend can be resolved.
It adds the correct paths to sys.path and provides helper functions to import
modules relative to the project structure.
"""
import os
import sys
import importlib
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("PathFixer")

def find_project_root():
    """
    Find the AILinux project root directory.
    
    Returns:
        str: Path to project root
    """
    # Start from current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try to find client directory
    while True:
        # Check if we're in the client directory
        if os.path.basename(current_dir) == 'client':
            return current_dir
            
        # Check if backend, frontend directories exist
        if os.path.isdir(os.path.join(current_dir, 'backend')) and \
           os.path.isdir(os.path.join(current_dir, 'frontend')):
            return current_dir
            
        # Move up one level
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # We've reached the root directory
            break
        current_dir = parent_dir
    
    # If we couldn't find the project root, return the directory of this script
    return os.path.dirname(os.path.abspath(__file__))

def fix_import_paths():
    """
    Add necessary paths to sys.path to ensure imports work correctly.
    """
    project_root = find_project_root()
    logger.info(f"Project root identified as: {project_root}")
    
    # Add important directories to sys.path
    paths_to_add = [
        project_root,
        os.path.join(project_root, 'backend'),
        os.path.join(project_root, 'client'),
        os.path.join(project_root, 'client', 'backend')
    ]
    
    for path in paths_to_add:
        if path not in sys.path and os.path.exists(path):
            sys.path.insert(0, path)
            logger.info(f"Added to sys.path: {path}")

def import_backend_module(module_name):
    """
    Safely import a backend module, trying different import paths if needed.
    
    Args:
        module_name: Name of the module to import
    
    Returns:
        module: Imported module or None if import failed
    """
    # Try direct import first
    try:
        module = importlib.import_module(module_name)
        return module
    except ImportError:
        pass
    
    # Try with backend prefix
    try:
        module = importlib.import_module(f"backend.{module_name}")
        return module
    except ImportError:
        pass
    
    # Try with client.backend prefix
    try:
        module = importlib.import_module(f"client.backend.{module_name}")
        return module
    except ImportError:
        logger.error(f"Failed to import module: {module_name}")
        return None

def main():
    """
    Run the path fixer to ensure imports work correctly.
    """
    fix_import_paths()
    
    # Test importing a critical module
    ai_model = import_backend_module('ai_model')
    if ai_model:
        logger.info("Successfully imported ai_model module")
        return True
    else:
        logger.error("Failed to import ai_model module")
        return False

if __name__ == "__main__":
    if main():
        print("Path fixing completed successfully")
        sys.exit(0)
    else:
        print("Path fixing failed")
        sys.exit(1)
