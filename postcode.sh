#!/bin/bash

# Function to display the menu
show_menu() {
  echo "-------------------------"
  echo "📂 File Search and Analysis"
  echo "-------------------------"
  echo "1) Search for *.js files"
  echo "2) Search for *.py files"
  echo "3) Search for *.html files"
  echo "4) Search for *.txt (requirements.txt)"
  echo "5) Post All (Run all searches and analyses)"
  echo "6) Exit"
  echo "-------------------------"
}

# Function to search for files based on extension
search_files() {
  local extension=$1
  local directory=~/ailinux
  
  # Exclude node_modules, dist, and build directories, and search for files with the given extension
  echo "📂 Searching for *.$extension files in $directory, excluding node_modules, dist, build..."

  # Search for files and display their contents
  files=$(find $directory -type f -name "*.$extension" ! -path "*/node_modules/*" ! -path "*/dist/*" ! -path "*/build/*")
  if [ -z "$files" ]; then
    echo "⚠ No $extension files found!"
  else
    # Use tee to log results
    echo "$files" | tee postconf.log
    
    # Display contents of each file
    for file in $files; do
      echo "📄 Displaying content of $file:"
      cat $file
      echo "------------------------"
    done
  fi

  echo "✅ Search completed. Results saved to postconf.log."
  
  # Always post file hierarchy after search
  analyze_hierarchy
}

# Function to search specifically for requirements.txt files
search_requirements_txt() {
  local directory=~/ailinux

  echo "📂 Searching for requirements.txt files in $directory, excluding node_modules, dist, build..."

  # Search for requirements.txt and display its contents
  files=$(find $directory -type f -name "requirements.txt" ! -path "*/node_modules/*" ! -path "*/dist/*" ! -path "*/build/*")
  if [ -z "$files" ]; then
    echo "⚠ No requirements.txt files found!"
  else
    # Use tee to log results
    echo "$files" | tee requirements_log.txt

    # Display contents of each file
    for file in $files; do
      echo "📄 Displaying content of $file:"
      cat $file
      echo "------------------------"
    done
  fi

  echo "✅ Search completed. Results saved to requirements_log.txt."
  
  # Always post file hierarchy after search
  analyze_hierarchy
}

# Function to analyze the data hierarchy excluding specific frameworks
analyze_hierarchy() {
  local directory=~/ailinux

  # Exclude node_modules, dist, and build directories
  echo "📂 Analyzing the directory hierarchy of $directory, excluding node_modules, dist, build..."

  # Fixing tee command to properly pipe the output
  tree -I "node_modules|dist|build" $directory --dirsfirst --noreport | tee hierarchy_analysis.log

  echo "✅ Hierarchy analysis completed. Results saved to hierarchy_analysis.log."
}

# Function to post all actions (search for all file types and analyze hierarchy)
post_all() {
  # Perform all file searches and analysis
  echo "📂 Starting Post All process..."

  # Search for .js files
  search_files "js"
  
  # Search for .py files
  search_files "py"
  
  # Search for .html files
  search_files "html"
  
  # Search for requirements.txt
  search_requirements_txt
  
  echo "✅ Post All process completed. All results saved in respective log files."
}

# Main script execution loop
while true; do
  # Show the menu
  show_menu
  
  # Get the user's choice
  read -p "Please select an option (1-6): " choice

  case $choice in
    1)
      # Search for .js files and display contents
      search_files "js"
      ;;
    2)
      # Search for .py files and display contents
      search_files "py"
      ;;
    3)
      # Search for .html files and display contents
      search_files "html"
      ;;
    4)
      # Search for *.txt files (specifically requirements.txt)
      search_requirements_txt
      ;;
    5)
      # Perform all searches and analysis (Post All)
      post_all
      ;;
    6)
      # Exit the script
      echo "Exiting the script. Goodbye!"
      exit 0
      ;;
    *)
      # Invalid choice
      echo "⚠ Invalid option. Please choose a valid option (1-6)."
      ;;
  esac
done
