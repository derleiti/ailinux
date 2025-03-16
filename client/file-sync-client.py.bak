"""
AILinux File Synchronization Client

This script synchronizes files between a local directory and the derleiti.de server.
It uses SFTP for secure file transfer and supports two-way synchronization.
"""
import os
import sys
import time
import logging
import json
import hashlib
import paramiko
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("sync_client.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SyncClient")

# Server connection settings
SERVER_HOST = os.getenv("SERVER_HOST", "derleiti.de")
SERVER_PORT = int(os.getenv("SERVER_PORT", 22))
SERVER_USERNAME = os.getenv("SERVER_USERNAME", "")
SERVER_PASSWORD = os.getenv("SERVER_PASSWORD", "")
SERVER_KEY_PATH = os.getenv("SERVER_KEY_PATH", "")

# Sync directories
LOCAL_DIR = os.getenv("LOCAL_SYNC_DIR", "./data")
REMOTE_DIR = os.getenv("REMOTE_SYNC_DIR", "/home/data")

# Sync configuration
SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL", 60))  # seconds
SYNC_MODE = os.getenv("SYNC_MODE", "two-way")  # "upload", "download", or "two-way"
EXCLUDE_PATTERNS = os.getenv("EXCLUDE_PATTERNS", ".git,.env,__pycache__,.DS_Store").split(",")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 100 * 1024 * 1024))  # 100 MB default limit


class FileSync:
    """File synchronization client for AILinux."""

    def __init__(self):
        """Initialize the file sync client."""
        self.ssh = None
        self.sftp = None
        self.connected = False
        self.manifest_path = os.path.join(LOCAL_DIR, ".sync_manifest.json")
        self.remote_manifest_path = os.path.join(REMOTE_DIR, ".sync_manifest.json")
        self.manifest = self._load_manifest()

        # Create local directory if it doesn't exist
        if not os.path.exists(LOCAL_DIR):
            os.makedirs(LOCAL_DIR)
            logger.info("Created local directory: %sLOCAL_DIR")

    def _load_manifest(self):
        """Load the sync manifest from file or create a new one."""
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Error loading manifest: %se")

        # Create a new manifest if none exists
        return {
            "last_sync": "",
            "files": {}
        }

    def _save_manifest(self):
        """Save the current manifest to file."""
        try:
            with open(self.manifest_path, 'w', encoding='utf-8') as f:
                json.dump(self.manifest, f, indent=2)
            logger.debug("Manifest saved locally")
        except Exception as e:
            logger.error("Error saving manifest: %se")

    def _get_file_hash(self, filepath):
        """Calculate MD5 hash of a file."""
        if not os.path.exists(filepath):
            return None

        # Skip large files
        if os.path.getsize(filepath) > MAX_FILE_SIZE:
            logger.warning("Skipping large file: %sfilepath")
            return "size_exceeded"

        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.error("Error calculating hash for %sfilepath: %se")
            return None

    def connect(self):
        """Connect to the remote server."""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect using password or key
            if SERVER_KEY_PATH:
                logger.info("Connecting to %sSERVER_HOST:%sSERVER_PORT using key authentication")
                self.ssh.connect(
                    SERVER_HOST,
                    port=SERVER_PORT,
                    username=SERVER_USERNAME,
                    key_filename=SERVER_KEY_PATH
                )
            else:
                logger.info(f"" +
                    "Connecting to {SERVER_HOST}:{SERVER_PORT} using password authentication")
                self.ssh.connect(
                    SERVER_HOST,
                    port=SERVER_PORT,
                    username=SERVER_USERNAME,
                    password=SERVER_PASSWORD
                )

            # Open SFTP connection
            self.sftp = self.ssh.open_sftp()

            # Create remote directory if it doesn't exist
            try:
                self.sftp.stat(REMOTE_DIR)
            except FileNotFoundError:
                # Execute mkdir -p equivalent
                stdin, stdout, stderr = self.ssh.exec_command(f"mkdir -p {REMOTE_DIR}")
                exit_status = stdout.channel.recv_exit_status()
                if exit_status != 0:
                    _error = stderr.read().decode().strip()
                    logger.error("Failed to create remote directory: %serror")
                    return False
                logger.info("Created remote directory: %sREMOTE_DIR")

            self.connected = True
            logger.info("Connected to server successfully")
            return True

        except Exception as e:
            logger.error("Connection error: %se")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from the remote server."""
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()
        self.connected = False
        logger.info("Disconnected from server")

    def _get_local_files(self):
        """Get a list of all local files with their last modified time and size."""
        files = {}
        for root, dirs, filenames in os.walk(LOCAL_DIR):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in EXCLUDE_PATTERNS)]

            for filename in filenames:
                # Skip excluded files
                if any(pattern in filename for pattern in EXCLUDE_PATTERNS):
                    continue

                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, LOCAL_DIR)

                # Skip the manifest file
                if rel_path == ".sync_manifest.json":
                    continue

                files[rel_path] = {
                    "modified": os.path.getmtime(filepath),
                    "size": os.path.getsize(filepath),
                    "hash": self._get_file_hash(filepath)
                }

        return files

    def _get_remote_files(self):
        """Get a list of all remote files with their last modified time and size."""
        if not self.connected:
            logger.error("Not connected to server")
            return {}

        try:
            # Download remote manifest if it exists
            try:
                self.sftp.get(self.remote_manifest_path, self.manifest_path + ".remote")
                with open(self.manifest_path + ".remote", 'r', encoding='utf-8') as f:
                    remote_manifest = json.load(f)
                os.remove(self.manifest_path + ".remote")
                return remote_manifest["files"]
            except FileNotFoundError:
                logger.info("Remote manifest not found. Scanning remote directory...")

            files = {}
            self._scan_remote_dir(REMOTE_DIR, files)
            return files

        except Exception as e:
            logger.error("Error getting remote files: %se")
            return {}

    def _scan_remote_dir(self, directory, files_dict, base_dir=None):
        """Recursively scan a remote directory."""
        if base_dir is None:
            base_dir = REMOTE_DIR

        try:
            file_list = self.sftp.listdir_attr(directory)

            for file_attr in file_list:
                filepath = os.path.join(directory, file_attr.filename)
                rel_path = os.path.relpath(filepath, base_dir)

                # Skip excluded files
                if any(pattern in file_attr.filename for pattern in EXCLUDE_PATTERNS):
                    continue

                # Skip the manifest file
                if rel_path == ".sync_manifest.json":
                    continue

                if stat.S_ISDIR(file_attr.st_mode):
                    # Recurse into subdirectories
                    self._scan_remote_dir(filepath, files_dict, base_dir)
                else:
                    # Store file info
                    files_dict[rel_path] = {
                        "modified": file_attr.st_mtime,
                        "size": file_attr.st_size,
                        "hash": None  # Cannot calculate hash without downloading
                    }
        except Exception as e:
            logger.error("Error scanning remote directory %sdirectory: %se")

    def _ensure_remote_dir(self, remote_path):
        """Ensure that a remote directory exists."""
        if not self.connected:
            return False

        try:
            dir_path = os.path.dirname(os.path.join(REMOTE_DIR, remote_path))
            if dir_path == REMOTE_DIR:
                return True

            try:
                self.sftp.stat(dir_path)
                return True
            except FileNotFoundError:
                # Execute mkdir -p equivalent
                stdin, stdout, stderr = self.ssh.exec_command(f"mkdir -p {dir_path}")
                exit_status = stdout.channel.recv_exit_status()
                if exit_status != 0:
                    _error = stderr.read().decode().strip()
                    logger.error("Failed to create remote directory %sdir_path: %serror")
                    return False
                logger.info("Created remote directory: %sdir_path")
                return True
        except Exception as e:
            logger.error("Error ensuring remote directory: %se")
            return False

    def _upload_file(self, rel_path):
        """Upload a file to the remote server."""
        if not self.connected:
            return False

        local_path = os.path.join(LOCAL_DIR, rel_path)
        remote_path = os.path.join(REMOTE_DIR, rel_path)

        # Skip files that are too large
        if os.path.getsize(local_path) > MAX_FILE_SIZE:
            logger.warning("Skipping upload of large file: %srel_path")
            return False

        try:
            # Ensure the remote directory exists
            if not self._ensure_remote_dir(rel_path):
                return False

            # Upload the file
            self.sftp.put(local_path, remote_path)
            logger.info("Uploaded file: %srel_path")

            # Update the manifest
            self.manifest["files"][rel_path] = {
                "modified": os.path.getmtime(local_path),
                "size": os.path.getsize(local_path),
                "hash": self._get_file_hash(local_path),
                "last_sync": datetime.now().isoformat()
            }

            return True
        except Exception as e:
            logger.error("Error uploading file %srel_path: %se")
            return False

    def _download_file(self, rel_path):
        """Download a file from the remote server."""
        if not self.connected:
            return False

        local_path = os.path.join(LOCAL_DIR, rel_path)
        remote_path = os.path.join(REMOTE_DIR, rel_path)

        try:
            # Ensure the local directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # Download the file
            self.sftp.get(remote_path, local_path)
            logger.info("Downloaded file: %srel_path")

            # Update the manifest
            self.manifest["files"][rel_path] = {
                "modified": os.path.getmtime(local_path),
                "size": os.path.getsize(local_path),
                "hash": self._get_file_hash(local_path),
                "last_sync": datetime.now().isoformat()
            }

            return True
        except Exception as e:
            logger.error("Error downloading file %srel_path: %se")
            return False

    def _delete_local_file(self, rel_path):
        """Delete a local file."""
        local_path = os.path.join(LOCAL_DIR, rel_path)
        try:
            if os.path.exists(local_path):
                os.remove(local_path)
                logger.info("Deleted local file: %srel_path")

                # Remove from manifest
                if rel_path in self.manifest["files"]:
                    del self.manifest["files"][rel_path]

                return True
            return False
        except Exception as e:
            logger.error("Error deleting local file %srel_path: %se")
            return False

    def _delete_remote_file(self, rel_path):
        """Delete a remote file."""
        if not self.connected:
            return False

        remote_path = os.path.join(REMOTE_DIR, rel_path)
        try:
            self.sftp.remove(remote_path)
            logger.info("Deleted remote file: %srel_path")

            # Remove from manifest
            if rel_path in self.manifest["files"]:
                del self.manifest["files"][rel_path]

            return True
        except Exception as e:
            logger.error("Error deleting remote file %srel_path: %se")
            return False

    def sync(self):
        """Synchronize files between local and remote directories."""
        if not self.connected:
            if not self.connect():
                return False

        try:
            # Get local and remote file listings
            local_files = self._get_local_files()
            remote_files = self._get_remote_files()

            # Files to upload (local but not remote, or newer locally)
            files_to_upload = []
            # Files to download (remote but not local, or newer remotely)
            files_to_download = []
            # Files to delete locally (deleted remotely in two-way sync)
            files_to_delete_local = []
            # Files to delete remotely (deleted locally in two-way sync)
            files_to_delete_remote = []

            # Compare local and remote files
            for rel_path, local_info in local_files.items():
                if rel_path not in remote_files:
                    # File exists locally but not remotely
                    files_to_upload.append(rel_path)
                elif local_info["hash"] != "size_exceeded":
                    # File exists in both places, check if local is newer
                    remote_info = remote_files[rel_path]

                    # If we have previous sync info, use it for comparison
                    if rel_path in self.manifest["files"]:
                        last_sync_info = self.manifest["files"][rel_path]

                        # If local file changed since last sync
                        if local_info["modified"] > last_sync_info.get("modified", 0):
                            files_to_upload.append(rel_path)
                        # If remote file doesn't have hash info, can't compare directly
                        elif remote_info.get("hash") is None:
                            if remote_info["modified"] > last_sync_info.get("modified", 0):
                                files_to_download.append(rel_path)
                    else:
                        # No sync history, just compare modification times
                        if local_info["modified"] > remote_info.get("modified", 0):
                            files_to_upload.append(rel_path)
                        else:
                            files_to_download.append(rel_path)

            # Check for files that exist remotely but not locally
            for rel_path in remote_files:
                if rel_path not in local_files:
                    # File exists remotely but not locally
                    if SYNC_MODE == "two-way" or SYNC_MODE == "download":
                        files_to_download.append(rel_path)
                    elif SYNC_MODE == "upload":
                        # In upload-only mode, delete remote files that don't exist locally
                        files_to_delete_remote.append(rel_path)

            # Check for files that were in the previous manifest but no longer exist
            for rel_path in list(self.manifest["files"].keys()):
                if rel_path not in local_files and rel_path not in remote_files:
                    # File has been deleted from both sides
                    del self.manifest["files"][rel_path]
                elif SYNC_MODE == "two-way":
                    if rel_path not in local_files and rel_path in remote_files:
                        # File was deleted locally but exists remotely
                        files_to_delete_remote.append(rel_path)
                    elif rel_path in local_files and rel_path not in remote_files:
                        # File was deleted remotely but exists locally
                        files_to_delete_local.append(rel_path)

            # Perform uploads
            if SYNC_MODE == "upload" or SYNC_MODE == "two-way":
                for rel_path in files_to_upload:
                    self._upload_file(rel_path)

            # Perform downloads
            if SYNC_MODE == "download" or SYNC_MODE == "two-way":
                for rel_path in files_to_download:
                    self._download_file(rel_path)

            # Perform local deletions (only in two-way mode)
            if SYNC_MODE == "two-way":
                for rel_path in files_to_delete_local:
                    self._delete_local_file(rel_path)

            # Perform remote deletions
            if SYNC_MODE == "upload" or SYNC_MODE == "two-way":
                for rel_path in files_to_delete_remote:
                    self._delete_remote_file(rel_path)

            # Update last sync time
            self.manifest["last_sync"] = datetime.now().isoformat()

            # Save the manifest
            self._save_manifest()

            # Upload the manifest to remote if in upload or two-way mode
            if SYNC_MODE == "upload" or SYNC_MODE == "two-way":
                try:
                    self.sftp.put(self.manifest_path, self.remote_manifest_path)
                    logger.debug("Manifest uploaded to remote server")
                except Exception as e:
                    logger.error("Error uploading manifest: %se")

            logger.info(f"" +
                "" +
                    "
                        "Sync completed: {len(files_to_upload)} uploaded, {len(files_to_download)} downloaded, "
                      f"" +
                          "" +
                              "
                                  "{len(files_to_delete_local)} deleted locally, {len(files_to_delete_remote)} deleted remotely")

            return True

        except Exception as e:
            logger.error("Error during sync: %se")
            return False
        finally:
            self._save_manifest()

    def run_sync_loop(self):
        """Run the sync process in a continuous loop."""
        logger.info("Starting sync loop with interval %sSYNC_INTERVAL seconds")
        logger.info("Sync mode: %sSYNC_MODE")
        logger.info("Local directory: %sLOCAL_DIR")
        logger.info("Remote directory: %sREMOTE_DIR")

        try:
            while True:
                logger.info("Starting sync iteration")
                success = self.sync()
                if not success:
                    logger.warning("Sync iteration failed")

                    # Reconnect on next iteration
                    self.disconnect()

                logger.info("Waiting %sSYNC_INTERVAL seconds until next sync")
                time.sleep(SYNC_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Sync loop interrupted by user")
        finally:
            self.disconnect()
            logger.info("Sync loop terminated")


def main():
    """Main function to run the file sync client."""
    import argparse

    parser = argparse.ArgumentParser(description="AILinux File Synchronization Client")
    parser.add_argument("--once", action="store_true", help="Run sync once and exit")
    parser.add_argument("--mode", choices=["upload", "download", "two-way"],
                        help="Sync mode (override .env setting)")
    parser.add_argument("--local-dir", help="Local directory path (override .env setting)")
    parser.add_argument("--remote-dir", help="Remote directory path (override .env setting)")

    args = parser.parse_args()

    # Override settings from command line arguments
    if args.mode:
        global SYNC_MODE
        SYNC_MODE = args.mode
        logger.info("Sync mode overridden from command line: %sSYNC_MODE")

    if args.local_dir:
        global LOCAL_DIR
        LOCAL_DIR = args.local_dir
        logger.info("Local directory overridden from command line: %sLOCAL_DIR")

    if args.remote_dir:
        global REMOTE_DIR
        REMOTE_DIR = args.remote_dir
        logger.info("Remote directory overridden from command line: %sREMOTE_DIR")

    # Create and run the sync client
    sync_client = FileSync()

    if args.once:
        # Run sync once and exit
        logger.info("Running sync once")
        success = sync_client.sync()
        sync_client.disconnect()
        sys.exit(0 if success else 1)
    else:
        # Run continuous sync loop
        sync_client.run_sync_loop()


if __name__ == "__main__":
    # Import here to avoid circular imports
    import stat
    main()
