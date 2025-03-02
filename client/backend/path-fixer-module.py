"""Path fixer for AILinux modules.

Ensures that modules can be imported regardless of where the script is run from.
"""
import os
import sys
import importlib
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
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
    logger.debug(f"Project root identified as: {project_root}")
    
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
            logger.debug(f"Added to sys.path: {path}")

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

def import_frontend_module(module_name):
    """
    Safely import a frontend module, trying different import paths if needed.
    
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
    
    # Try with frontend prefix
    try:
        module = importlib.import_module(f"frontend.{module_name}")
        return module
    except ImportError:
        pass
    
    # Try with client.frontend prefix
    try:
        module = importlib.import_module(f"client.frontend.{module_name}")
        return module
    except ImportError:
        logger.error(f"Failed to import module: {module_name}")
        return None

# Run the fixer when the module is imported
fix_import_paths()

if __name__ == "__main__":
    # When run directly, print the sys.path and test an import
    print("Current sys.path:")
    for path in sys.path:
        print(f"  {path}")
    
    # Test importing a module
    print("\nTesting imports:")
    for module_name in ['ai_model', 'app', 'config']:
        module = import_backend_module(module_name)
        status = "SUCCESS" if module else "FAILED"
        print(f"  {module_name}: {status}")
