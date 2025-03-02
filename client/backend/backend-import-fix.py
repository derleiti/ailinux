"""
Enhanced Import Path Fixer for AILinux Backend

This module ensures that all imports in the AILinux backend can be resolved
regardless of where the script is run from. It provides robust path handling
and fallback mechanisms.
"""
import os
import sys
import importlib
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("import_fix.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ImportFixer")

def find_project_root():
    """
    Find the AILinux project root directory using multiple detection strategies.
    
    Returns:
        str: Path to project root
    """
    # Start from current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Strategy 1: Check for directory names
    search_path = current_dir
    for _ in range(5):  # Look up to 5 levels
        if os.path.basename(search_path) == 'client':
            logger.info(f"Found project root (client directory): {search_path}")
            return search_path
            
        parent = os.path.dirname(search_path)
        if parent == search_path:  # Reached filesystem root
            break
        search_path = parent
    
    # Strategy 2: Look for key directories
    search_path = current_dir
    for _ in range(5):  # Look up to 5 levels
        if (os.path.isdir(os.path.join(search_path, 'backend')) and 
            os.path.isdir(os.path.join(search_path, 'frontend'))):
            logger.info(f"Found project root (backend/frontend directories): {search_path}")
            return search_path
            
        if os.path.isdir(os.path.join(search_path, 'client')) and \
           os.path.isdir(os.path.join(search_path, 'client', 'backend')):
            logger.info(f"Found project root (client/backend directories): {search_path}")
            return search_path
            
        parent = os.path.dirname(search_path)
        if parent == search_path:  # Reached filesystem root
            break
        search_path = parent
    
    # Strategy 3: Look for specific files
    search_path = current_dir
    key_files = ['start.js', 'start.sh', 'requirements.txt']
    
    for _ in range(5):  # Look up to 5 levels
        if any(os.path.isfile(os.path.join(search_path, f)) for f in key_files):
            logger.info(f"Found project root (key file detected): {search_path}")
            return search_path
            
        parent = os.path.dirname(search_path)
        if parent == search_path:  # Reached filesystem root
            break
        search_path = parent
    
    # If all else fails, return current directory
    logger.warning(f"Could not determine project root, using current directory: {current_dir}")
    return current_dir

def fix_import_paths():
    """
    Add necessary paths to sys.path to ensure imports work correctly,
    with multiple fallback strategies.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Find project root using our robust method
        project_root = find_project_root()
        
        # Define key paths to add
        paths_to_add = [
            project_root,
            os.path.join(project_root, 'backend'),
            os.path.join(project_root, 'client'),
            os.path.join(project_root, 'client', 'backend'),
            os.path.join(project_root, 'client', 'frontend'),
            os.path.dirname(os.path.abspath(__file__))  # Current directory
        ]
        
        # Add paths to sys.path if they exist and aren't already in sys.path
        for path in paths_to_add:
            if path and os.path.exists(path) and path not in sys.path:
                sys.path.insert(0, path)
                logger.info(f"Added to sys.path: {path}")
        
        # Create .pth file for more permanent fix
        try:
            import site
            site_packages = site.getsitepackages()[0]
            pth_file = os.path.join(site_packages, "ailinux.pth")
            
            with open(pth_file, "w") as f:
                for path in paths_to_add:
                    if path and os.path.exists(path):
                        f.write(f"{path}\n")
            
            logger.info(f"Created .pth file at {pth_file}")
        except Exception as e:
            logger.warning(f"Failed to create .pth file: {e}")
            # Not critical to continue
        
        logger.info("Import paths fixed successfully")
        return True
    except Exception as e:
        logger.error(f"Error fixing import paths: {e}")
        logger.debug(traceback.format_exc())
        return False

def import_with_fallbacks(module_name, possible_prefixes=None):
    """
    Attempt to import a module with multiple fallback strategies.
    
    Args:
        module_name: Name of the module to import
        possible_prefixes: List of possible prefixes to try (e.g. 'backend.', 'client.backend.')
    
    Returns:
        The imported module or None if all import attempts fail
    """
    if possible_prefixes is None:
        possible_prefixes = ['', 'backend.', 'client.backend.', 'client.']
    
    # Try direct import first
    for prefix in possible_prefixes:
        full_name = f"{prefix}{module_name}" if prefix else module_name
        try:
            module = importlib.import_module(full_name)
            logger.info(f"Successfully imported {full_name}")
            return module
        except ImportError:
            continue
        except Exception as e:
            logger.warning(f"Error importing {full_name}: {e}")
            continue
    
    # All import attempts failed
    logger.error(f"Failed to import module: {module_name}")
    return None

def verify_imports():
    """
    Verify that key modules can be imported after fixing paths.
    
    Returns:
        bool: True if all key modules can be imported, False otherwise
    """
    key_modules = ['ai_model', 'app', 'websocket-client']
    success = True
    
    for module_name in key_modules:
        try:
            # Normalize module name for import
            normalized_name = module_name.replace('-', '_')
            module = import_with_fallbacks(normalized_name)
            if module is None:
                logger.warning(f"Could not import {module_name}")
                success = False
        except Exception as e:
            logger.error(f"Error verifying import for {module_name}: {e}")
            success = False
    
    return success

def get_available_paths():
    """
    Get a diagnostic list of all available paths in sys.path.
    
    Returns:
        list: List of paths in sys.path
    """
    return sys.path

def main():
    """
    Run the import path fixing process and verify imports.
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Starting import path fixing")
    
    # Fix import paths
    fix_result = fix_import_paths()
    if not fix_result:
        logger.warning("Import path fixing encountered issues")
    
    # Verify imports
    verify_result = verify_imports()
    if not verify_result:
        logger.warning("Some imports could not be verified")
    
    # Get diagnostic info
    paths = get_available_paths()
    logger.info(f"Current sys.path has {len(paths)} entries")
    
    return fix_result and verify_result

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)
