"""Module docstring missing."""
import os

# Hauptverzeichnis definieren (anpassen, falls nötig)
root_dir = "./"

# Ordner, die ausgeschlossen werden sollen
excluded_dirs = {"models", "__pycache__", "node_modules"}

# Log-Dateien ausschließen
excluded_files = {".log"}

# Pfad zur Logdatei
log_file_path = "project_code_analysis_1.log"

# Nur frontend- und backend-Verzeichnisse berücksichtigen
allowed_dirs = {"frontend", "backend"}

with open(log_file_path, "w", encoding='utf-8') as log_file:
    for root, dirs, files in os.walk(root_dir):
        # Filtere die Verzeichnisse, die ausgeschlossen werden sollen
        # und beschränke die Analyse auf frontend und backend
        dirs[:] = [d for d in dirs if d not in excluded_dirs and d in allowed_dirs]

        # Überprüfe, ob der aktuelle Pfad frontend oder backend ist
        current_dir = os.path.basename(root)
        if current_dir not in allowed_dirs:
            continue

        for file in files:
            # Nur .html-Dateien, keine Log-Dateien
            if file.endswith(".html") and not any(file.endswith(ext) for ext in excluded_files):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding='utf-8') as f:
                    log_file.write(f"\n--- {file_path} ---\n")
                    log_file.write(f.read())
