"""Module docstring missing."""
import os

# Define the correct directory for analysis
directory = '/home/zombie/ailinux'

# Verify the directory exists
if os.path.exists(directory):
    # Get all file paths and their sizes
    file_sizes = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            file_sizes.append((file_path, file_size))

    # Sort by size in descending order
    file_sizes.sort(key=lambda x: x[1], reverse=True)

    # Show top 20 largest files
    top_20_files = file_sizes[:20]
    top_20_files
else:
    "Directory does not exist or cannot be accessed"
