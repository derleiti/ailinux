#!/bin/bash

# Function to display the menu
show_menu() {
  echo "-------------------------"
  echo "📂 File Search and Analysis"
  echo "-------------------------"
  echo "1) Search for *.js files"
  echo "2) Search for *.py files"
  echo "3) Search for *.html files"
  echo "4) Search for all file types"
  echo "5) Exit"
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
    echo "⚠️ No $extension files found!"
  else
.    echo "$files" | tee postconf.log
    
    # Display contents of each file
    for file in $files; do
      echo "📄 Displaying content of $file:"
      cat $file
      echo "------------------------"
    done
  fi

  echo "✅ Search completed. Results saved to postconf.log."
  echo "📂 Displaying the entire file system hierarchy (excluding node_modules, dist, build)..."
  tree -I "node_modules|dist|build" $directory --dirsfirst --noreport
}

# Function to analyze the data hierarchy excluding specific frameworks
analyze_hierarchy() {
  local directory=~/ailinux

  # Exclude node_modules, dist, and build directories
  echo "📂 Analyzing the directory hierarchy of $directory, excluding node_modules, dist, build..."

  tree -I "node_modules|dist|build" $directory --dirsfirst --noreport | tee hierarchy_analysis.log

  echo "✅ Hierarchy analysis completed. Results saved to hierarchy_analysis.log."
  echo "📂 Displaying the entire file system hierarchy (excluding node_modules, dist, build)..."
  tree -I "node_modules|dist|build" $directory --dirsfirst --noreport
}

# Main script execution loop
while true; do
  # Show the menu
  show_menu
  
  # Get the user's choice
  read -p "Please select an option (1-5): " choice

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
      # Search for all file types (i.e., without a specific extension)
      search_files "js"
      search_files "py"
      search_files "html"
      ;;
    5)
      # Exit the script
      echo "Exiting the script. Goodbye!"
      exit 0
      ;;
    *)
      # Invalid choice
      echo "⚠️ Invalid option. Please choose a valid option (1-5)."
      ;;
  esac
done
