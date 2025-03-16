#!/usr/bin/env python3
"""
Duplicate Code Finder and Refactorer

This script identifies and helps refactor duplicate code across Python files.
It analyzes pylint R0801 warnings and suggests how to extract common code
into shared modules.

Usage:
    python duplicate_code_finder.py optimization.log
"""
import os
import re
# # Potential unused import: import sys  # removed: W0611
# # Potential unused import: import argparse  # removed: W0611
from typing import List, Dict, Set, Tuple, Optional
import logging
# # Potential unused import: import difflib  # removed: W0611


class DuplicateCodeSection:
    """Represents a section of duplicate code identified by pylint."""

    def __init__(self, files: List[str], lines: List[str], line_ranges: Dict[str, Tuple[int, int]]):
        self.files = files
        self.lines = lines
        self.line_ranges = line_ranges  # file -> (start_line, end_line)
        self.similarity_score = 0.0

    def __repr__(self) -> str:
        file_list = ", ".join(self.files)
        return f"Duplicate code across {len(self.files)} files: {file_list}"


class DuplicateCodeFinder:
    """Analyzes pylint output for duplicate code and suggests refactoring."""

    def __init__(self, log_file: str, output_file: Optional[str] = None):
        self.log_file = log_file
        self.output_file = output_file
        self.duplicate_sections: List[DuplicateCodeSection] = []

        # Set up logging
        self.logger = logging.getLogger('duplicate_code_finder')
        self.logger.setLevel(logging.INFO)

        # Add console handler
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        self.logger.addHandler(console)

        # Add file handler if output file is specified
        if output_file:
            file_handler = logging.FileHandler(output_file, 'w')
            file_handler.setLevel(logging.INFO)
            self.logger.addHandler(file_handler)

    def parse_log_file(self) -> List[DuplicateCodeSection]:
        """Parse the pylint log file to find R0801 (duplicate code) warnings."""
        duplicate_sections = []
        current_files = []
        current_lines = []
        current_ranges = {}

        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Look for the start of a duplicate code section
            if "Similar lines in" in line and "R0801" in line:
                # Extract files involved
                match = re.search(r"Similar lines in (\d+) files", line)
                if not match:
                    i += 1
                    continue

                num_files = int(match.group(1))
                current_files = []
                current_lines = []
                current_ranges = {}

                # Parse the file information
                for j in range(i+1, min(i+1+num_files*2, len(lines))):
                    file_line = lines[j].strip()

                    # Extract file and line range information
                    match = re.search(r"==([^:]+):(\[\d+:\d+\])", file_line)
                    if match:
                        file_path = match.group(1)
                        line_range_str = match.group(2)
                        line_range_match = re.search(r"\[(\d+):(\d+)\]", line_range_str)
                        if line_range_match:
                            start_line = int(line_range_match.group(1))
                            end_line = int(line_range_match.group(2))
                            current_files.append(file_path)
                            current_ranges[file_path] = (start_line, end_line)

                # Get the duplicate code content
                duplicate_content_start = i + 1 + num_files*2
                for j in range(duplicate_content_start, len(lines)):
                    content_line = lines[j].strip()
                    if not content_line or "(" in content_line or ")" in content_line:
                        break
                    current_lines.append(content_line)

                # Create a DuplicateCodeSection if we have sufficient information
                if current_files and current_lines and current_ranges:
                    section = DuplicateCodeSection(
                        files=current_files,
                        lines=current_lines,
                        line_ranges=current_ranges
                    )
                    duplicate_sections.append(section)

                # Skip to after the parsed section
                i = duplicate_content_start + len(current_lines)
            else:
                i += 1

        self.duplicate_sections = duplicate_sections
        return duplicate_sections

    def analyze_duplicates(self) -> None:
        """Analyze duplicate code sections and provide refactoring suggestions."""
        if not self.duplicate_sections:
            self.logger.info("No duplicate code sections found.")
            return

        self.logger.info("Found %slen(self.duplicate_sections) duplicate code sections.")

        # Group duplicates by the files they appear in
        duplicates_by_files: Dict[str, List[DuplicateCodeSection]] = {}

        for section in self.duplicate_sections:
            # Sort files to ensure consistent ordering
            key = ";".join(sorted(section.files))
            if key not in duplicates_by_files:
                duplicates_by_files[key] = []
            duplicates_by_files[key].append(section)

        # Process each group of files with duplicate code
        for files_key, sections in duplicates_by_files.items():
            files = files_key.split(";")

            self.logger.info("\n" + "="*80)
            self.logger.info("Duplicate code across %slen(files) files:")
            for file in files:
                self.logger.info("  - %sfile")

            # Check if files are in the same directory
            directories = {os.path.dirname(file) for file in files}
            common_dir = os.path.commonpath(directories) if len(directories) > 1 else list(directories)[0]

            # Suggest a module name for extracted code
            module_name = self._suggest_module_name(files)

            # Determine where to place the new module
            module_path = os.path.join(common_dir, f"{module_name}.py")

            self.logger.info("\nSuggested refactoring:")
            self.logger.info("  1. Create a new module: %smodule_path")
            self.logger.info("  2. Extract the following code to the new module:")

            # Display the duplicate code
            for i, section in enumerate(sections):
                self.logger.info("\n  --- Duplicate section %si+1 ---")
                for line in section.lines:
                    self.logger.info("  %sline")

            # Suggest # Potential unused import: import statements
            self.logger.info("\n  3. Replace the duplicate code with imports:")
            for file in files:
                rel_path = os.path.relpath(module_path, os.path.dirname(file))
                rel_path = rel_path.replace(".py", "").replace("\\", "/")
                if not rel_path.startswith("."):
                    rel_path = f".{rel_path}"
                self.logger.info("  In %sfile: from %srel_path # Potential unused import: import *")

    def generate_refactoring_code(self) -> Optional[str]:
        """Generate refactoring code for the most significant duplicate section."""
        if not self.duplicate_sections:
            return None

        # Find the largest duplicate section
        largest_section = max(self.duplicate_sections, key=lambda s: len(s.lines))

        # Extract files and determine common directory
        files = largest_section.files
        if not files:
            return None

        directories = {os.path.dirname(file) for file in files}
        common_dir = os.path.commonpath(directories) if len(directories) > 1 else list(directories)[0]

        # Suggest module name
        module_name = self._suggest_module_name(files)
        module_path = os.path.join(common_dir, f"{module_name}.py")

        # Create the new module content
        module_content = '"""\n'
        module_content += f"{module_name} - Common functionality extracted from duplicate code.\n\n"
        module_content += "
            "This module contains functionality that was previously duplicated across:\n"
        for file in files:
            module_content += f"- {file}\n"
        module_content += '"""\n\n'

        # Add imports that may be needed
        module_content += "# Potential unused import: import os\n"
        module_content += "# Potential unused import: import logging\n"
        module_content += "from typing import Dict, List, Optional, Any\n\n\n"

        # Add the duplicate code
        module_content += "\n".join(largest_section.lines)

        return {
            "module_path": module_path,
            "content": module_content,
            "files_to_update": files,
            "code_to_replace": largest_section.lines,
            "line_ranges": largest_section.line_ranges
        }

    def _suggest_module_name(self, files: List[str]) -> str:
        """Suggest a suitable name for the new module based on file names."""
        common_words = set()

        # Extract base filenames without extensions
        basenames = [os.path.basename(file).replace('.py', '') for file in files]

        if not basenames:
            return "common_utils"

        # Find common words in filenames
        for basename in basenames:
            # Split by common separators and lowercase
            words = re.split(r'[_\-.]', basename.lower())

            if not common_words:
                common_words