"""
Python Version Compatibility Check and Patching for AILinux

This module checks Python version compatibility and applies patches
to ensure AILinux works correctly with Python 3.12+
"""
import sys
import os
import re
import logging
import subprocess
import importlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("PythonVersionFix")

def check_python_version():
    """Check the Python version and determine if patching is needed."""
    major, minor = sys.version_info[:2]
    logger.info(f"Detected Python {major}.{minor}")
    
    # Python 3.9-3.11 is fully compatible
    if major == 3 and 9 <= minor <= 11:
        logger.info("Python version is fully compatible with AILinux")
        return False, "Compatible"
    
    # Python 3.12+ may have compatibility issues with some libraries
    if major == 3 and minor >= 12:
        logger.warning(f"Python {major}.{minor} may have compatibility issues with some libraries")
        return True, f"Python {major}.{minor}"
    
    # Legacy Python versions
    if major < 3 or (major == 3 and minor < 9):
        logger.warning(f"Python {major}.{minor} is older than recommended. AILinux works best with Python 3.9-3.11")
        return False, "Legacy"
    
    return False, "Unknown"

def locate_uuid_module():
    """Find the path to the uuid module in the current Python environment."""
    try:
        import uuid
        return uuid.__file__
    except ImportError:
        logger.error("uuid module not found")
        return None

def patch_uuid_module():
    """Patch the uuid module for Python 3.12+ compatibility."""
    uuid_path = locate_uuid_module()
    if not uuid_path:
        return False
    
    logger.info(f"Found uuid module at: {uuid_path}")
    
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
    
    # Replace the problematic line
    # Pattern: if not 0 <= time_low < 1<<32L:
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
        logger.info("No patching needed for uuid module")
        return True

def verify_flask_imports():
    """Verify that Flask and its dependencies can be imported."""
    try:
        import flask
        import werkzeug
        logger.info(f"Flask version: {flask.__version__}")
        logger.info(f"Werkzeug version: {werkzeug.__version__}")
        return True
    except ImportError as e:
        logger.error(f"Flask import failed: {e}")
        return False
    except SyntaxError as e:
        logger.error(f"Flask syntax error: {e}")
        return False

def install_compatible_packages():
    """Install compatible versions of Flask and dependencies."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", 
                              "flask>=2.0.0,<3.0.0", 
                              "werkzeug>=2.0.0,<3.0.0",
                              "flask-cors>=3.0.0"],
                              stdout=subprocess.PIPE)
        logger.info("Installed compatible Flask and dependencies")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install packages: {e}")
        return False

def main():
    """Run the compatibility check and apply fixes if needed."""
    needs_patching, version_status = check_python_version()
    
    if needs_patching and version_status.startswith("Python 3.12"):
        logger.info("Applying Python 3.12+ compatibility patches...")
        
        if patch_uuid_module():
            logger.info("Successfully applied patches for Python 3.12+")
            
            # Reload uuid module to ensure patches take effect
            if 'uuid' in sys.modules:
                del sys.modules['uuid']
            
            # Verify the patches worked
            if verify_flask_imports():
                logger.info("Flask is now working correctly!")
                return True
            else:
                logger.warning("Flask still has issues after patching")
                return install_compatible_packages()
        else:
            logger.error("Failed to apply patches")
            return False
    elif version_status == "Compatible":
        # Nothing needs to be done for compatible versions
        return verify_flask_imports()
    else:
        # For legacy versions, just try to verify Flask works
        return verify_flask_imports()

if __name__ == "__main__":
    if main():
        print("Python environment is now compatible with AILinux")
        sys.exit(0)
    else:
        print("Failed to make Python environment compatible")
        sys.exit(1)
