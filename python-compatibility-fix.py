"""
AILinux Python Compatibility Fix

This module patches critical libraries for Python 3.12+ compatibility and ensures
proper initialization of the backend services.
"""
import os
import sys
import re
import logging
# Potential unused import: import importlib
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("CompatibilityFix")

def get_python_version():
    """Get the current Python version information."""
    major, minor, micro = sys.version_info[:3]
    return {
        "major": major,
        "minor": minor,
        "micro": micro,
        "version_str": f"{major}.{minor}.{micro}",
        "is_compatible": (major == 3 and 9 <= minor <= 11),
        "needs_patching": (major == 3 and minor >= 12)
    }

def patch_uuid_module():
    """Patch the UUID module for Python 3.12+ compatibility."""
    try:
        # Find the uuid module
        import uuid
        uuid_path = uuid.__file__
        
        if not uuid_path:
            logger.error("Could not locate uuid module")
            return False
            
        logger.info(f"Found uuid module at: {uuid_path}")
        
        # Create backup if it doesn't exist
        backup_path = f"{uuid_path}.backup"
        if not os.path.exists(backup_path):
            import shutil
            shutil.copy2(uuid_path, backup_path)
            logger.info(f"Created backup at: {backup_path}")
        
        # Read the content
        with open(uuid_path, 'r') as f:
            content = f.read()
        
        # Check for Python 3.12+ incompatible code patterns
        patterns = [
            (r'if not 0 <= time_low < 1<<32L:', 'if not 0 <= time_low < 1<<32:'),
            (r'if not 0 <= node < 1<<48L:', 'if not 0 <= node < 1<<48:'),
            (r'if not 0 <= clock_seq < 1<<14L:', 'if not 0 <= clock_seq < 1<<14:')
        ]
        
        patched = False
        for pattern, replacement in patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                patched = True
                logger.info(f"Patched pattern: {pattern}")
        
        if patched:
            with open(uuid_path, 'w') as f:
                f.write(content)
            logger.info("Successfully patched uuid module")
            
            # Reload the module to apply changes
            if 'uuid' in sys.modules:
                del sys.modules['uuid']
                import uuid
            return True
        else:
            logger.info("No patches needed for uuid module")
            return True
            
    except Exception as e:
        logger.error(f"Failed to patch uuid module: {e}")
        return False

def fix_flask_import_issues():
    """Fix # Potential unused import: import issues with Flask and its dependencies."""
    try:
        # First, try to # Potential unused import: import flask to check if it works
        try:
            import flask
            logger.info(f"Flask version {flask.__version__} is working correctly")
            return True
        except SyntaxError as e:
            logger.warning(f"Flask has a syntax error: {e}")
        except ImportError as e:
            logger.warning(f"Flask import error: {e}")
            
        # If we're here, we need to fix Flask
        logger.info("Attempting to fix Flask installation...")
        
        # Install compatible versions
        cmd = [
            sys.executable, 
            "-m", 
            "pip", 
            "install", 
            "--upgrade",
            "flask==2.0.1",
            "werkzeug==2.0.1",
            "Jinja2==3.0.1",
            "flask-cors==3.0.10"
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Failed to install Flask: {result.stderr}")
            return False
            
        logger.info("Flask installed successfully")
        
        # Try importing Flask again
        try:
            import flask
            logger.info(f"Flask version {flask.__version__} is now working correctly")
            return True
        except Exception as e:
            logger.error(f"Still having issues with Flask: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error fixing Flask: {e}")
        return False

def fix_path_issues():
    """Fix Python path issues to ensure modules can be found."""
    try:
        # Get the base directory
        base_dir = Path(__file__).parent.parent
        
        # Add directories to Python path
        dirs_to_add = [
            str(base_dir),
            str(base_dir / "backend"),
            str(base_dir / "client"),
            str(base_dir / "client/backend")
        ]
        
        for directory in dirs_to_add:
            if os.path.exists(directory) and directory not in sys.path:
                sys.path.insert(0, directory)
                logger.info(f"Added to Python path: {directory}")
        
        return True
    except Exception as e:
        logger.error(f"Error fixing path issues: {e}")
        return False

def fix_all_issues():
    """Fix all compatibility issues."""
    version_info = get_python_version()
    logger.info(f"Python version: {version_info['version_str']}")
    
    fixes_applied = []
    
    # Fix path issues
    if fix_path_issues():
        fixes_applied.append("path_issues")
    
    # Apply patches for Python 3.12+
    if version_info["needs_patching"]:
        logger.info("Python 3.12+ detected, applying compatibility patches...")
        if patch_uuid_module():
            fixes_applied.append("uuid_module")
    
    # Fix Flask import issues
    if fix_flask_import_issues():
        fixes_applied.append("flask_imports")
    
    return {
        "success": len(fixes_applied) > 0,
        "python_version": version_info["version_str"],
        "fixes_applied": fixes_applied
    }

if __name__ == "__main__":
    result = fix_all_issues()
    
    if result["success"]:
        print(f"Successfully applied fixes: {', '.join(result['fixes_applied'])}")
        sys.exit(0)
    else:
        print("Failed to apply fixes")
        sys.exit(1)
