"""Module docstring missing."""
import os
import subprocess
# import sys
  # entfernt: W0611

# Funktion zum Hinzufügen von Docstrings zu Modulen und Funktionen
def add_docstrings(file_path):
    try:
        with open(file_path, 'r', encoding="utf-8") as file:
            lines = file.readlines()
    except UnicodeDecodeError:
        # Falls utf-8 Fehler auftreten, versuche es mit einer anderen Kodierung
        with open(file_path, 'r', encoding="ISO-8859-1", errors='ignore') as file:
            lines = file.readlines()

    # Überprüfen und Hinzufügen von fehlenden Docstrings
    if lines and lines[0].startswith("import"):
        if not any(line.strip().startswith('"""') for line in lines):
            lines.insert(0, '"""Module docstring missing."""\n')

    with open(file_path, 'w', encoding="utf-8") as file:
        file.writelines(lines)

# Funktion zur Analyse und Aktualisierung von Dateien
def analyze_and_update_files(base_path):
    # Durchlaufe alle Dateien im Projektverzeichnis
    for dirpath, dirnames, filenames in os.walk(base_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)

            # Wenn die Datei eine Python-Datei ist, füge Docstrings hinzu
            if file_path.endswith('.py'):
                print(f"Überprüfe Datei: {file_path}")
                add_docstrings(file_path)

# Funktion zum Überprüfen und Anpassen der Berechtigungen
def adjust_permissions(base_path):
    for dirpath, dirnames, filenames in os.walk(base_path):
        for dirname in dirnames:
            dir_full_path = os.path.join(dirpath, dirname)
            os.chmod(dir_full_path, 0o775)
            print(f"Setze Berechtigungen für Verzeichnis: {dir_full_path}")

        for filename in filenames:
            file_full_path = os.path.join(dirpath, filename)
            os.chmod(file_full_path, 0o664)
            print(f"Setze Berechtigungen für Datei: {file_full_path}")

# Funktion zum Ausführen von Pylint zur Code-Überprüfung
def run_pylint(base_path):
    print("Starte Pylint zur Code-Überprüfung...")
    try:
        result = subprocess.run(['pylint', base_path], capture_output=True, text=True)
        if result.returncode == 0:
            print("Pylint hat keine Fehler gefunden.")
        else:
            print(f"Pylint Fehler:\n{result.stdout}")
            with open("pylint_report.log", "w") as log_file:
                log_file.write(result.stdout)
            print("Fehlerbericht wurde in 'pylint_report.log' gespeichert.")
    except Exception as e:
        print(f"Fehler beim Ausführen von Pylint: {e}")

# Hauptfunktion des Skripts
def main():
    base_dir = "/home/zombie/ailinux"

    # Überprüfe und analysiere die Dateien im Projektverzeichnis
    print("Projekt wird überprüft und aktualisiert...")
    analyze_and_update_files(base_dir)

    # Passe Berechtigungen an
    print("Berechtigungen werden angepasst...")
    adjust_permissions(base_dir)

    # Führe Pylint aus, um den Code zu überprüfen
    run_pylint(base_dir)

if __name__ == "__main__":
    main()
