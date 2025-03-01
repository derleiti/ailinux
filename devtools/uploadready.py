import os
import subprocess
import logging
from typing import Optional

def sync_with_github(
    username: str, 
    repo_name: str, 
    auth_key: Optional[str] = None, 
    use_pat: bool = False,
    branch: str = "main"
) -> bool:
    """
    Synchronizes the local repository with GitHub with enhanced error handling and logging.
    
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
            import datetime
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
        logger.info(f"Pull result: {pull_result.stdout}")
        logger.info(f"Push result: {push_result.stdout}")

        if pull_result.returncode == 0 and push_result.returncode == 0:
            logger.info("GitHub synchronization completed successfully.")
            return True
        else:
            logger.error(f"Sync failed. Pull stderr: {pull_result.stderr}")
            logger.error(f"Sync failed. Push stderr: {push_result.stderr}")
            return False

    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {e}")
        logger.error(f"Command output: {e.output}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during GitHub synchronization: {e}")
        return False

def main():
    """Interactive GitHub synchronization helper."""
    try:
        # Prompt for GitHub connection details
        username = input("GitHub Username: ").strip()
        repo_name = input("GitHub Repository Name: ").strip()
        auth_key = input("SSH Authentication Key or Personal Access Token (optional): ").strip() or None
        use_pat = input("Use Personal Access Token? (y/n): ").lower() == 'y'
        branch = input("Branch to sync (default: main): ").strip() or "main"

        # Attempt synchronization
        success = sync_with_github(username, repo_name, auth_key, use_pat, branch)
        
        # Provide user feedback
        if success:
            print("✓ GitHub synchronization completed successfully.")
        else:
            print("✗ GitHub synchronization failed. Check github_sync.log for details.")

    except Exception as e:
        print(f"Error in GitHub synchronization: {e}")

if __name__ == "__main__":
    main()
