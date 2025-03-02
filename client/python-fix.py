def check_python_compatibility():
    """
    Check Python version compatibility with required libraries.
    Returns True if compatible, False otherwise.
    """
    import sys
    import logging

    logger = logging.getLogger("CompatibilityCheck")
    
    major, minor = sys.version_info[:2]
    logger.info(f"Detected Python {major}.{minor}")
    
    # Check for compatibility issues with Flask
    if major == 3 and minor > 11:
        logger.warning(f"Python {major}.{minor} may have compatibility issues with Flask")
        logger.warning("Recommended Python version: 3.9-3.11")
        return False
        
    return True

# Add to start.js or app.py before initializing Flask
if not check_python_compatibility():
    print("WARNING: Incompatible Python version detected. Some features may not work correctly.")
    print("Please consider using Python 3.9-3.11 for full compatibility.")
