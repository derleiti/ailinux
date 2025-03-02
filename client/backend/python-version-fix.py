"""
Python Version Compatibility Fix for AILinux Backend

This script fixes compatibility issues with Python 3.12+ and the Flask/UUID modules.
It should be executed before starting the backend server.
"""
import sys
import os
import re
import logging
import importlib
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("python_fix.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PythonFix")

def check_python_version():
    """Check Python version and determine if patching is needed."""
    major, minor = sys.version_info[:2]
    logger.info(f"Detected Python {major}.{minor}")
    
    # Python 3.9-3.11 is fully compatible
    if major == 3 and 9 <= minor <= 11:
        logger.info("Python version is fully compatible")
        return False, "Compatible"
    
    # Python 3.12+ needs patching
    if major == 3 and minor >= 12:
        logger.warning(f"Python {major}.{minor} requires patching for compatibility")
        return True, f"Python {major}.{minor}"
    
    # Legacy Python versions
    if major < 3 or (major == 3 and minor < 9):
        logger.warning(f"Python {major}.{minor} is older than recommended (3.9-3.11)")
        return False, "Legacy"
    
    return False, "Unknown"

def locate_uuid_module():
    """Find the uuid.py module in the current Python environment."""
    try:
        import uuid
        path = getattr(uuid, "__file__", None)
        if path:
            logger.info(f"UUID module found at: {path}")
            return path
        
        # Try to find it in standard lib locations
        for base_path in sys.path:
            potential_path = os.path.join(base_path, "uuid.py")
            if os.path.isfile(potential_path):
                logger.info(f"UUID module found at: {potential_path}")
                return potential_path
        
        logger.error("UUID module file not found")
        return None
    except ImportError:
        logger.error("UUID module not found")
        return None

def patch_uuid_module():
    """Patch the uuid module for Python 3.12+ compatibility."""
    uuid_path = locate_uuid_module()
    if not uuid_path:
        return False
    
    # Create backup
    backup_path = f"{uuid_path}.backup"
    if not os.path.exists(backup_path):
        try:
            import shutil
            shutil.copy2(uuid_path, backup_path)
            logger.info(f"Created backup at: {backup_path}")
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    # Read file content
    try:
        with open(uuid_path, 'r') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read uuid module: {e}")
        return False
    
    # Replace the problem line - long integer suffix 'L'
    pattern = r'if not 0 <= time_low < 1<<32L:'
    replacement = 'if not 0 <= time_low < 1<<32:'
    
    if re.search(pattern, content):
        # Apply patch
        patched_content = re.sub(pattern, replacement, content)
        
        try:
            with open(uuid_path, 'w') as f:
                f.write(patched_content)
            logger.info(f"Successfully patched uuid module for Python 3.12+ compatibility")
            return True
        except Exception as e:
            logger.error(f"Failed to write patched uuid module: {e}")
            return False
    else:
        # If the pattern is not found, there might be a different issue
        # or the module has already been patched
        logger.info("No patching needed for uuid module (pattern not found)")
        return True

def fix_import_paths():
    """Fix Python import paths to ensure modules can be found."""
    # Determine base directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    client_dir = os.path.join(base_dir, "client")
    backend_dir = os.path.join(client_dir, "backend")
    
    # Add important paths to sys.path
    paths_to_add = [
        base_dir,
        client_dir,
        backend_dir,
        os.path.join(client_dir, "frontend")
    ]
    
    for path in paths_to_add:
        if os.path.exists(path) and path not in sys.path:
            sys.path.insert(0, path)
            logger.info(f"Added path to sys.path: {path}")
    
    # Create .pth file in site-packages to make this permanent
    try:
        import site
        site_packages = site.getsitepackages()[0]
        pth_file = os.path.join(site_packages, "ailinux.pth")
        
        with open(pth_file, "w") as f:
            for path in paths_to_add:
                if os.path.exists(path):
                    f.write(f"{path}\n")
        
        logger.info(f"Created .pth file at {pth_file}")
        return True
    except Exception as e:
        logger.warning(f"Failed to create .pth file: {e}")
        # This is not critical, as we've already updated sys.path
        return True

def install_dependencies():
    """Install required dependencies to ensure Flask works correctly."""
    packages = [
        "flask>=2.0.0,<3.0.0",  # Flask 2.x is compatible with all Python 3.9-3.12
        "flask-cors>=3.0.0",    # For CORS support
        "werkzeug>=2.0.0,<3.0.0", # Werkzeug needs to be compatible with Flask
        "python-dotenv>=0.19.0",  # For .env file support
        "psutil>=5.9.0"         # For system monitoring
    ]
    
    try:
        logger.info("Installing required dependencies...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade"] + packages,
            stderr=subprocess.STDOUT
        )
        logger.info("Successfully installed dependencies")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False

def verify_flask_works():
    """Verify that Flask can be imported successfully."""
    try:
        # Try to import flask to ensure it works
        import flask
        logger.info(f"Flask {flask.__version__} imported successfully")
        return True
    except ImportError as e:
        logger.error(f"Failed to import Flask: {e}")
        return False
    except SyntaxError as e:
        logger.error(f"Syntax error importing Flask: {e}")
        return False

def main():
    """Main function to run all fixes."""
    logger.info("Starting Python compatibility fixes for AILinux backend")
    
    # Step 1: Check Python version
    needs_patching, version_status = check_python_version()
    
    # Step 2: Fix UUID module if needed
    if needs_patching:
        logger.info("Applying UUID module patch for Python 3.12+")
        if not patch_uuid_module():
            logger.warning("UUID module patching failed")
    
    # Step 3: Fix import paths
    if not fix_import_paths():
        logger.warning("Import path fixing failed")
    
    # Step 4: Install dependencies
    install_dependencies()
    
    # Step 5: Verify Flask works
    if verify_flask_works():
        logger.info("Flask is working correctly!")
        return True
    else:
        logger.warning("Flask verification failed")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("All fixes applied successfully!")
        sys.exit(0)
    else:
        logger.error("Failed to apply all fixes")
        sys.exit(1)
