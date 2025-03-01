import os
import subprocess
import logging
import datetime
import argparse
import sys
from typing import Optional, Tuple, Dict, Any, List


def sync_with_github(
    username: str, 
    repo_name: str, 
    auth_key: Optional[str] = None, 
    use_pat: bool = False,
    branch: str = "main"
) -> bool:
    """
    Synchronizes the local repository with GitHub with enhanced error handling and logging.
    
    This function handles the complete GitHub synchronization workflow including:
    - Validation of inputs and authentication methods
    - Configuring git settings
    - Committing any uncommitted changes
    - Fetching updates from the remote repository
    - Pulling and pushing changes with appropriate error handling
    
    Args:
        username (str): GitHub username
        repo_name (str): GitHub repository name
        auth_key (Optional[str]): Authentication key (SSH or Personal Access Token)
        use_pat (bool): Flag to indicate whether to use Personal Access Token
        branch (str): Branch to synchronize (default: 'main')
    
    Returns:
        bool: True if synchronization was successful, False otherwise
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='github_sync.log'
    )
    logger = logging.getLogger(__name__)

    try:
        # Validate inputs
        if not username or not repo_name:
            logger.error("GitHub username or repository name is missing")
            return False

        # Prepare GitHub URL
        if use_pat:
            if not auth_key:
                logger.error("Personal Access Token is required when use_pat is True")
                return False
            github_url = f"https://{username}:{auth_key}@github.com/{username}/{repo_name}.git"
        else:
            # For SSH, ensure the key is set up correctly
            if not os.path.exists(os.path.expanduser("~/.ssh/id_rsa")):
                logger.error("SSH key not found. Please set up SSH authentication.")
                return False
            github_url = f"git@github.com:{username}/{repo_name}.git"

        # Ensure git configuration
        subprocess.run(["git", "config", "--global", "pull.rebase", "true"], check=True)
        subprocess.run(["git", "config", "--global", "push.autoSetupRemote", "true"], check=True)

        # Check if git repository exists
        try:
            subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], 
                           check=True, 
                           capture_output=True, 
                           text=True)
        except subprocess.CalledProcessError:
            logger.error("Not a git repository. Please initialize git first.")
            return False

        # Check for uncommitted changes
        status_result = subprocess.run(
            ["git", "status", "--porcelain"], 
            capture_output=True, 
            text=True
        )
        
        # Stage and commit changes if there are any
        if status_result.stdout.strip():
            logger.info("Uncommitted changes detected. Staging and committing.")
            subprocess.run(["git", "add", "."], check=True)
            
            # Create a timestamp-based commit message
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"Automated commit: {timestamp}"
            
            subprocess.run(["git", "commit", "-m", commit_message], check=True)

        # Ensure the correct branch is checked out
        subprocess.run(["git", "checkout", branch], check=True)

        # Fetch and pull with rebase
        subprocess.run(["git", "fetch", "origin", branch], check=True)
        pull_result = subprocess.run(
            ["git", "pull", "--rebase", "origin", branch], 
            capture_output=True, 
            text=True
        )

        # Push changes
        push_result = subprocess.run(
            ["git", "push", "origin", branch], 
            capture_output=True, 
            text=True
        )

        # Log detailed results
        logger.info("Pull result: %s", pull_result.stdout)
        logger.info("Push result: %s", push_result.stdout)

        if pull_result.returncode == 0 and push_result.returncode == 0:
            logger.info("GitHub synchronization completed successfully.")
            return True
        else:
            logger.error("Sync failed. Pull stderr: %s", pull_result.stderr)
            logger.error("Sync failed. Push stderr: %s", push_result.stderr)
            return False

    except subprocess.CalledProcessError as e:
        logger.error("Git command failed: %s", e)
        logger.error("Command output: %s", e.output)
        return False
    except (ValueError, ConnectionError) as e:
        # Specific handling for network errors and value errors
        logger.error("Network or connection error during GitHub synchronization: %s", e)
        return False
    except Exception as e:
        # More specific exception handling for unexpected errors
        logger.error("Unexpected error during GitHub synchronization: %s", e)
        return False


def validate_inputs(username: str, repo_name: str, auth_key: Optional[str], use_pat: bool) -> Tuple[bool, str]:
    """
    Validate user inputs for GitHub synchronization.
    
    Args:
        username (str): GitHub username
        repo_name (str): GitHub repository name
        auth_key (Optional[str]): Authentication key
        use_pat (bool): Flag indicating PAT usage
        
    Returns:
        Tuple[bool, str]: Success status and error message if any
    """
    if not username or not username.strip():
        return False, "Username cannot be empty"
    
    if not repo_name or not repo_name.strip():
        return False, "Repository name cannot be empty"
    
    if use_pat and not auth_key:
        return False, "Personal Access Token is required when using PAT authentication"
    
    return True, ""


def run_pylint(files: Optional[List[str]] = None) -> bool:
    """
    Run pylint on specified files or the entire project.
    
    Args:
        files: Optional list of files to check, defaults to all Python files
        
    Returns:
        bool: True if pylint succeeded with no errors, False otherwise
    """
    try:
        print("Running pylint code quality check...")
        
        # Determine which files to check
        if not files:
            # Get all Python files in the current directory
            cmd = ["find", ".", "-name", "*.py", "-not", "-path", "*/\\.*"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            files = result.stdout.strip().split('\n')
        
        # Run pylint on the files
        cmd = ["pylint"] + files + ["--output-format=text", "--reports=y"]
        
        # Save results to a log file
        with open("optimization.log", "w") as log_file:
            result = subprocess.run(cmd, stdout=log_file, stderr=subprocess.PIPE, text=True)
        
        # Check results
        if result.returncode == 0:
            print("✓ No pylint issues found.")
            return True
        else:
            print(f"✗ Pylint found issues. Check optimization.log for details.")
            # Print a summary of the issues
            with open("optimization.log", "r") as log_file:
                summary = log_file.readlines()[-10:]  # Last 10 lines typically contain the summary
                for line in summary:
                    print(line.strip())
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Error running pylint: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during pylint check: {e}")
        return False


def file_update(start_dir: str = ".", backup: bool = True) -> bool:
    """
    Analyze directory structure and handle large files.
    
    This function:
    1. Recursively scans the directory structure including all subfolders
    2. Creates directory_structure.json with the complete file structure
    3. Identifies files larger than 99MB and saves them to large_files.json
    4. Updates .gitignore to include these large files
    
    Args:
        start_dir: Directory to start the analysis from (default: current directory)
        backup: Whether to create backups of modified files
        
    Returns:
        bool: True if all operations succeeded, False otherwise
    """
    try:
        print(f"Starting recursive file structure analysis from {start_dir}")
        print("This will scan all subfolders and files in the directory tree.")
        
        # Structure to hold directory information
        dir_structure = {}
        # List to hold large files (>99MB)
        large_files = []
        # Size threshold for large files (99MB in bytes)
        size_threshold = 99 * 1024 * 1024
        # Counter for statistics
        stats = {
            "total_dirs": 0,
            "total_files": 0,
            "total_size": 0
        }
        
        # Function to scan directory recursively
        def scan_directory(path, structure):
            """Recursively scan directory and build structure dict"""
            nonlocal stats
            
            try:
                items = os.listdir(path)
                stats["total_dirs"] += 1
                
                for item in items:
                    full_path = os.path.join(path, item)
                    rel_path = os.path.relpath(full_path, start_dir)
                    
                    # Skip hidden files/folders
                    if item.startswith('.'):
                        continue
                        
                    if os.path.isdir(full_path):
                        # It's a directory
                        structure[item] = {"type": "directory", "contents": {}}
                        scan_directory(full_path, structure[item]["contents"])
                    else:
                        # It's a file
                        try:
                            file_size = os.path.getsize(full_path)
                            stats["total_files"] += 1
                            stats["total_size"] += file_size
                            
                            # Add to structure
                            structure[item] = {
                                "type": "file", 
                                "size": file_size,
                                "size_human": format_size(file_size)
                            }
                            
                            # Check if it's a large file
                            if file_size > size_threshold:
                                large_files.append({
                                    "path": rel_path,
                                    "size": file_size,
                                    "size_human": format_size(file_size)
                                })
                        except Exception as e:
                            print(f"Error processing file {full_path}: {e}")
                            structure[item] = {"type": "file", "error": str(e)}
            except PermissionError:
                print(f"Permission denied: Cannot access {path}")
                structure["__error__"] = "Permission denied"
            except Exception as e:
                print(f"Error scanning directory {path}: {e}")
                structure["__error__"] = str(e)
        
        # Helper function to format file sizes for human readability
        def format_size(size_bytes):
            """Format bytes to human-readable size"""
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size_bytes < 1024.0 or unit == 'TB':
                    return f"{size_bytes:.2f} {unit}"
                size_bytes /= 1024.0
        
        # Start the scan
        print("Scanning directories and files...")
        scan_directory(start_dir, dir_structure)
        
        # Print statistics
        print(f"\nScan complete!")
        print(f"Found {stats['total_dirs']} directories and {stats['total_files']} files")
        print(f"Total data size: {format_size(stats['total_size'])}")
        print(f"Found {len(large_files)} files larger than 99MB")
        
        # Save directory structure to JSON
        structure_file = "directory_structure.json"
        
        # Backup if needed
        if backup and os.path.exists(structure_file):
            backup_path = f"{structure_file}.bak"
            print(f"Creating backup of {structure_file} at {backup_path}")
            import shutil
            shutil.copy2(structure_file, backup_path)
        
        # Save the new structure
        import json
        with open(structure_file, 'w') as f:
            json.dump({
                "stats": {
                    "total_directories": stats["total_dirs"],
                    "total_files": stats["total_files"],
                    "total_size_bytes": stats["total_size"],
                    "total_size_human": format_size(stats["total_size"]),
                    "scan_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "structure": dir_structure
            }, f, indent=2)
        print(f"✓ Complete directory structure saved to {structure_file}")
        
        # Save large files list to JSON
        large_files_file = "large_files.json"
        
        # Backup if needed
        if backup and os.path.exists(large_files_file):
            backup_path = f"{large_files_file}.bak"
            print(f"Creating backup of {large_files_file} at {backup_path}")
            import shutil
            shutil.copy2(large_files_file, backup_path)
        
        # Save the large files list
        with open(large_files_file, 'w') as f:
            json.dump({
                "count": len(large_files),
                "threshold": "99MB",
                "threshold_bytes": size_threshold,
                "files": large_files
            }, f, indent=2)
        print(f"✓ Found {len(large_files)} large files (>99MB), saved to {large_files_file}")
        
        # Update .gitignore with large files
        gitignore_path = ".gitignore"
        gitignore_lines = []
        
        # Read existing .gitignore if it exists
        if os.path.exists(gitignore_path):
            # Backup if needed
            if backup:
                backup_path = f"{gitignore_path}.bak"
                print(f"Creating backup of {gitignore_path} at {backup_path}")
                import shutil
                shutil.copy2(gitignore_path, backup_path)
            
            with open(gitignore_path, 'r') as f:
                gitignore_lines = [line.strip() for line in f.readlines()]
        
        # Add large files header if needed
        if gitignore_lines and gitignore_lines[-1] != "":
            gitignore_lines.append("")
        
        if len(large_files) > 0 and "# Large files (>99MB)" not in gitignore_lines:
            gitignore_lines.append("# Large files (>99MB)")
        
        # Check and add large files that aren't already in .gitignore
        added_count = 0
        for file_info in large_files:
            file_path = file_info["path"]
            if file_path not in gitignore_lines:
                gitignore_lines.append(file_path)
                added_count += 1
        
        # Write updated .gitignore
        with open(gitignore_path, 'w') as f:
            f.write("\n".join(gitignore_lines))
            # Ensure file ends with newline
            if gitignore_lines and not gitignore_lines[-1].endswith('\n'):
                f.write("\n")
        
        if added_count > 0:
            print(f"✓ Added {added_count} large files to .gitignore")
        else:
            print("✓ No new large files to add to .gitignore")
        
        return True
        
    except Exception as e:
        print(f"Error during file update: {e}")
        import traceback
        traceback.print_exc()
        return False


def restore_file(file_path: str) -> bool:
    """
    Restore a file from its backup.
    
    Args:
        file_path: Path to the file to restore
        
    Returns:
        bool: True if restoration succeeded, False otherwise
    """
    try:
        backup_path = f"{file_path}.bak"
        
        # Check if backup exists
        if not os.path.exists(backup_path):
            print(f"Error: Backup file {backup_path} does not exist.")
            return False
        
        # Restore from backup
        print(f"Restoring {file_path} from backup...")
        with open(backup_path, 'r') as src, open(file_path, 'w') as dst:
            dst.write(src.read())
        
        print(f"✓ File {file_path} restored successfully.")
        return True
        
    except Exception as e:
        print(f"Error restoring file {file_path}: {e}")
        return False


def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="GitHub sync tool with file management and code quality checks")
    
    # GitHub sync options
    parser.add_argument("--github", action="store_true", help="Sync with GitHub")
    
    # File management options
    parser.add_argument("--file-update", action="store_true", 
                       help="Analyze directory structure and handle large files")
    parser.add_argument("--start-dir", type=str, default=".",
                       help="Starting directory for file analysis (default: current directory)")
    parser.add_argument("--no-backup", action="store_true", help="Don't create backups when updating files")
    parser.add_argument("--restore-file", type=str, help="Restore a file from backup")
    
    # Code quality options
    parser.add_argument("--pylint", action="store_true", help="Run pylint on the codebase")
    parser.add_argument("--check-files", type=str, nargs="+", help="Specific files to check with pylint")
    
    return parser.parse_args()


def main():
    """
    Main function that handles command line arguments and executes the appropriate actions.
    
    This function provides a command-line interface for:
    1. Running pylint code quality checks
    2. Updating files with backup creation
    3. Restoring files from backups
    4. Synchronizing with GitHub repositories
    
    The program will exit after completing file operations or pylint checks without
    proceeding to GitHub sync if those operations were requested.
    """
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Handle pylint check
        if args.pylint:
            run_pylint(args.check_files)
            # Exit after pylint check, don't proceed to GitHub sync
            return
            
        # Handle file update
        if args.file_update:
            file_update(args.start_dir, not args.no_backup)
            # Exit after file update, don't proceed to GitHub sync
            return
            
        # Handle file restore
        if args.restore_file:
            restore_file(args.restore_file)
            # Exit after file restore, don't proceed to GitHub sync
            return
            
        # If --github flag is provided or no specific operation was requested, 
        # proceed with GitHub sync
        if args.github or (not args.pylint and not args.file_update and not args.restore_file):
            # Prompt for GitHub connection details
            username = input("GitHub Username: ").strip()
            repo_name = input("GitHub Repository Name: ").strip()
            auth_key = input("SSH Authentication Key or Personal Access Token (optional): ").strip() or None
            use_pat = input("Use Personal Access Token? (y/n): ").lower() == 'y'
            branch = input("Branch to sync (default: main): ").strip() or "main"

            # Validate inputs
            is_valid, error_msg = validate_inputs(username, repo_name, auth_key, use_pat)
            if not is_valid:
                print(f"Error: {error_msg}")
                return

            # Attempt synchronization
            success = sync_with_github(username, repo_name, auth_key, use_pat, branch)
            
            # Provide user feedback
            if success:
                print("✓ GitHub synchronization completed successfully.")
            else:
                print("✗ GitHub synchronization failed. Check github_sync.log for details.")
        else:
            print("No operation specified. Use --help to see available options.")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    sys.exit(0 if main() is None else 1)
