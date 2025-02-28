cd ~/ailinux/frontend/ && cat *.log
cd ~/ailinux/backend/ && cat *.log
cd ~/ailinux/
=======
#!/bin/bash

# Define the directories to check
frontend_dir="$HOME/ailinux/frontend"
backend_dir="$HOME/ailinux/backend"
ailinux_dir="$HOME/ailinux"

# Define the logs to exclude
exclude_logs=("postcode.log" "bigfiles.log" "hierarchy_analysis.log")

# Function to list logs excluding specified files
function list_logs_excluding {
  local dir=$1
  local exclude_logs=("${!2}")

  for log in $(ls $dir/*.log); do
    # Check if the file is in the exclusion list
    if [[ ! " ${exclude_logs[@]} " =~ " $(basename $log) " ]]; then
      cat $log
    fi
  done
}

# Show logs from frontend directory
echo "Frontend logs:"
list_logs_excluding "$frontend_dir" exclude_logs[@]

# Show logs from backend directory
echo "Backend logs:"
list_logs_excluding "$backend_dir" exclude_logs[@]

# Show logs from the main directory
echo "Main logs:"
list_logs_excluding "$ailinux_dir" exclude_logs[@]
