#!/bin/bash

# Directory to analyze
TARGET_DIR="$1"

# Size threshold in MB (can be changed as needed)
SIZE_THRESHOLD=100

# Check if the directory is passed as argument
if [ -z "$TARGET_DIR" ]; then
    echo "Usage: $0 <directory_to_analyze>"
    exit 1
fi

# Check if the directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "Directory $TARGET_DIR does not exist!"
    exit 1
fi

# Output file for large files
LOG_FILE="bigfiles.log"

# Initialize or clear the log file
> "$LOG_FILE"

# Find large files greater than SIZE_THRESHOLD MB and write to the log file
echo "Searching for files larger than ${SIZE_THRESHOLD}MB in $TARGET_DIR..." > "$LOG_FILE"
find "$TARGET_DIR" -type f -exec du -h {} + | awk -v threshold="$SIZE_THRESHOLD" '
    {
        # Extract the size in MB from the output
        size=$1
        file=$2
        gsub("M", "", size)
        gsub("G", "", size)
        
        if (size > threshold) {
            print "Large file found: " file ", Size: " $1 >> "'"$LOG_FILE"'"
        }
    }
'

# Inform user about the completion of the search
echo "File analysis complete. Large files have been written to $LOG_FILE."
