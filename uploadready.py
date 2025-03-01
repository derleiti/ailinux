"""
uploadready - Modulbeschreibung.
"""

import os
import json
import subprocess
# import shutil
  # entfernt: W0611
import sys
from pathlib import Path

# Hilfsfunktionen

def get_directory_structure(rootdir):
    """Erstellt eine rekursive Dateistruktur mit Größe und speichert sie im JSON-Format."""
    directory_structure = {}
    for dirpath, dirnames, filenames in os.walk(rootdir):
        dir_info = {}
        total_size = 0
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            file_size = os.path.getsize(filepath)
            total_size += file_size
            dir_info[filename] = {"size": file_size, "path": filepath}

        directory_structure[dirpath] = {"files": dir_info, "size": total_size}
    return directory_structure

def save_to_json(data, filename):
    """Speichert die gegebene Datenstruktur in einer JSON-Datei."""
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4)

def restore_directory_structure(data, rootdir):
    """Stellt die Dateistruktur wieder her und löscht nicht mehr vorhandene Dateien."""
    existing_files = set()

    # Alle Dateien, die laut JSON existieren sollen
    for dirpath, dir_info in data.items():
        for filename, file_info in dir_info["files"].items():
            existing_files.add(os.path.join(dirpath, filename))

    # Durchsucht das Verzeichnis und löscht Dateien, die nicht in der JSON-Struktur vorhanden sind
    for dirpath, dirnames, filenames in os.walk(rootdir):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if file_path not in existing_files:
                os.remove(file_path)  # Lösche die Datei

        # Lösche leere Verzeichnisse, die nicht mehr benötigt werden
        if not os.listdir(dirpath):
            os.rmdir(dirpath)

    # Stelle Dateien und Verzeichnisse wieder her, die in der JSON-Datei existieren
    for dirpath, dir_info in data.items():
        os.makedirs(dirpath, exist_ok=True)  # Stelle sicher, dass das Verzeichnis existiert
        for filename, file_info in dir_info["files"].items():
            file_path = os.path.join(dirpath, filename)
            if not os.path.exists(file_path):
                open(file_path, 'w', encoding='utf-8').close()  # Erstelle leere Dateien

            os.utime(file_path, None)  # Setze Zeitstempel, ohne die Datei zu ändern

def find_large_files(directory_structure, size_threshold=99 * 1024 * 1024):
    """Findet alle Dateien größer als eine gegebene Größe (in Bytes)."""
    large_files = {}
    for dirpath, dir_info in directory_structure.items():
        for filename, file_info in dir_info["files"].items():
            if file_info["size"] > size_threshold:
                large_files[filename] = file_info
    return large_files

def add_to_gitignore(large_files):
    """Fügt die großen Dateien zur .gitignore hinzu."""
    gitignore_path = Path(".gitignore")
    with open(gitignore_path, "a", encoding='utf-8') as gitignore:
        for filename in large_files:
            gitignore.write(f"{filename}\n")

def run_pylint():
    """Führt pylint für bestimmte Dateitypen aus und speichert das Ergebnis in eine Logdatei."""
    files_to_check = []
    for root, dirs, files in os.walk('.'):
        # Ausschließen des node_modules-Ordners
        if 'node_modules' in dirs:
            dirs.remove('node_modules')
        for file in files:
            if file.endswith(('.py', '.js', '.html')):
                files_to_check.append(os.path.join(root, file))

    # Führe pylint auf den Dateien aus, aber nur wenn es Dateien gibt
    if files_to_check:
        result = subprocess.run(['pylint'] + files_to_check, capture_output=True, text=True)
        with open("optimization.log", "w", encoding='utf-8') as log_file:
            log_file.write(result.stdout)
    else:
        print("Keine Dateien zum Prüfen gefunden.")

def sync_with_github(username, repo_name, ssh_key, use_pat=False):
    """Synchronisiert das lokale Repository mit GitHub über SSH oder PAT und führt einen Merge durch, wenn nötig."""
    try:
        # GitHub-URL vorbereiten
        if use_pat:
            github_url = f"https://{username}:{ssh_key}@github.com/{username}/{repo_name}.git"
        else:
            github_url = f"git@github.com:{username}/{repo_name}.git"

        # Konfiguriere Git, um nur Fast-Forward-Merges zu erlauben
        subprocess.run(["git", "config", "--global", "pull.ff", "only"], check=True)

        # Pull mit --no-ff um Merge durchzuführen, wenn Branches divergieren
        subprocess.run(["git", "pull", "--no-ff", github_url], check=True)  # Merging erzwingen

        subprocess.run(["git", "add", "."], check=True)  # Alle Änderungen hinzufügen
        subprocess.run(["git", "commit", "-m", "Automated commit"], check=True)  # Commit
        subprocess.run(["git", "push", github_url], check=True)  # Push zum Remote-Repository

    except subprocess.CalledProcessError as e:
        print(f"Error während GitHub-Synchronisierung: {e}")
        # Falls der Fehler bei der Authentifizierung liegt, frage nach dem PAT
        if "fatal: Authentifizierung" in str(e):
            print("Fehler bei der Authentifizierung. Bitte prüfe deinen SSH-Schlüssel oder Personal Access Token.")
        else:
            print(f"Git Fehler: {str(e)}")

# Hauptfunktionalität

def main():
    """Hauptfunktion zur Steuerung des Programms."""
    if "--file-update" in sys.argv:
        directory_structure = get_directory_structure(os.getcwd())
        save_to_json(directory_structure, "directory_structure.json")

        # Finden und speichern der großen Dateien
        large_files = find_large_files(directory_structure)
        save_to_json(large_files, "large_files.json")

        # Gitignore aktualisieren
        add_to_gitignore(large_files)

    if "--restore-file" in sys.argv:
        try:
            with open("directory_structure.json", "r", encoding='utf-8') as f:
                directory_structure = json.load(f)
            restore_directory_structure(directory_structure, os.getcwd())
        except FileNotFoundError:
            print("Fehler: directory_structure.json konnte nicht gefunden werden.")
        except json.JSONDecodeError:
            print("Fehler: directory_structure.json enthält ungültiges JSON.")

    if "--pylint" in sys.argv:
        run_pylint()

    if "--github" in sys.argv:
        # Abfrage der GitHub-Verbindungsdaten
        username = input("GitHub Username: ")
        repo_name = input("GitHub Repository Name: ")
        ssh_key = input("SSH Authentication Key or Personal Access Token: ")
        use_pat = input("Do you want to use a PAT? (y/n): ").lower() == 'y'

        sync_with_github(username, repo_name, ssh_key, use_pat)

# Skript ausführen
if __name__ == "__main__":
    main()
