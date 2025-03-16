#!/usr/bin/env python3
"""
Pylint Code Patcher

Dieses Skript liest pylint-Optimierungen aus einer Log-Datei
und wendet automatische Korrekturen auf den ursprünglichen Code an.
"""

import re
import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set


class PylintIssue:
    """Repräsentiert ein pylint-Problem."""

    def __init__(self, file_path: str, line_num: int, code: str, message: str):
        self.file_path = file_path
        self.line_num = line_num
        self.code = code  # z.B. C0103, E0611
        self.message = message

    def __repr__(self) -> str:
        return f"{self.file_path}:{self.line_num} [{self.code}] {self.message}"


class CodeFixer:
    """Klasse zum Beheben von pylint-Problemen im Code."""

    def __init__(self, issues: List[PylintIssue], dry_run: bool = False, log_file: str = None):
        self.issues = issues
        self.dry_run = dry_run
        self.file_cache: Dict[str, List[str]] = {}
        self.fixes_applied = 0
        self.skipped_issues = 0
        self.fixed_issues: List[PylintIssue] = []
        self.unfixed_issues: List[PylintIssue] = []

        # Setup logging
        self.logger = logging.getLogger('pylint_patcher')
        self.logger.setLevel(logging.INFO)

        # Console handler
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        self.logger.addHandler(console)

        # File handler (if log_file is provided)
        if log_file:
            file_handler = logging.FileHandler(log_file, mode='w')
            file_handler.setLevel(logging.INFO)
            self.logger.addHandler(file_handler)

    def load_file(self, file_path: str) -> List[str]:
        """Lädt eine Datei in den Cache, wenn sie nicht bereits geladen ist."""
        if file_path not in self.file_cache:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.file_cache[file_path] = file.readlines()
        return self.file_cache[file_path]

    def save_file(self, file_path: str) -> None:
        """Speichert die geänderten Dateiinhalte."""
        if self.dry_run:
            print(f"[DRY RUN] Würde {file_path} speichern")
        else:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(self.file_cache[file_path])
            print(f"Gespeichert: {file_path}")

    def fix_unused_import(self, issue: PylintIssue) -> bool:
        """Entfernt unbenutzte Importe (W0611)."""
        lines = self.load_file(issue.file_path)
        line = lines[issue.line_num - 1]

        # Extract the unused import name from the message
        match = re.search(r"Unused import (\w+)", issue.message)
        if not match:
            return False

        unused_import = match.group(1)

        # Handle different import styles
        if re.match(rf"^\s*import\s+{unused_import}\s*$", line):
            # Direct import (import unused)
            lines[issue.line_num - 1] = f"# {line}  # entfernt: {issue.code}\n"
        elif re.match(rf"^\s*from\s+[\w.]+\s+import\s+{unused_import}\s*$", line):
            # Single import from module (from module import unused)
            lines[issue.line_num - 1] = f"# {line}  # entfernt: {issue.code}\n"
        elif re.search(rf"from\s+[\w.]+\s+import\s+[^,]+,\s*{unused_import}(\s*,|$)", line):
            # Part of a multi-import (from module import used, unused, other)
            if re.search(rf"{unused_import},", line):
                # Unused import followed by comma
                lines[issue.line_num - 1] = line.replace(f"{unused_import}, ", "")
            elif re.search(rf",\s*{unused_import}", line):
                # Unused import preceded by comma
                lines[issue.line_num - 1] = line.replace(f", {unused_import}", "")

        return True

    def fix_trailing_whitespace(self, issue: PylintIssue) -> bool:
        """Entfernt Leerzeichen am Zeilenende (C0303)."""
        lines = self.load_file(issue.file_path)
        line = lines[issue.line_num - 1]
        fixed_line = line.rstrip() + '\n'

        if fixed_line != line:
            lines[issue.line_num - 1] = fixed_line
            return True

        return False

    def fix_missing_docstring(self, issue: PylintIssue) -> bool:
        """Fügt fehlende Docstrings hinzu (C0111, C0112, C0103)."""
        if not ("Missing docstring" in issue.message or "docstring" in issue.message.lower()):
            return False

        lines = self.load_file(issue.file_path)
        line = lines[issue.line_num - 1]

        # Erkennen, ob es eine Funktion, Klasse oder Modul ist
        is_func = "function" in issue.message.lower() or "def " in line
        is_class = "class" in issue.message.lower() or "class " in line
        is_module = "module" in issue.message.lower() or issue.line_num == 1

        indent = len(line) - len(line.lstrip())
        indent_str = ' ' * indent

        if is_module and issue.line_num == 1:
            # Module docstring
            docstring = '"""\nModulbeschreibung.\n"""\n\n'
            lines.insert(0, docstring)
            return True
        elif is_func and "def " in line:
            # Function docstring
            func_name = re.search(r'def\s+(\w+)', line)
            if func_name:
                name = func_name.group(1)
                docstring = f'{indent_str}"""
                    "\n{indent_str}Beschreibung für Funktion {name}.\n{indent_str}"""\n'
                lines.insert(issue.line_num, docstring)
                return True
        elif is_class and "class " in line:
            # Class docstring
            class_name = re.search(r'class\s+(\w+)', line)
            if class_name:
                name = class_name.group(1)
                docstring = f'{indent_str}"""" +
                    "\n{indent_str}Beschreibung für Klasse {name}.\n{indent_str}"""\n'
                lines.insert(issue.line_num, docstring)
                return True

        return False

    def fix_line_too_long(self, issue: PylintIssue) -> bool:
        """Verkürzt zu lange Zeilen (C0301)."""
        if "Line too long" not in issue.message:
            return False

        lines = self.load_file(issue.file_path)
        line = lines[issue.line_num - 1]

        # Spezialfall: String aufteilen
        if '"' in line or "'" in line:
            # Einfache Aufteilung von Strings
            for quote in ['"', "'"]:
                pattern = f'({quote}[^{quote}]*{quote})'
                strings = re.findall(pattern, line)
                for string in strings:
                    if len(string) > 30:  # Nur lange Strings aufteilen
                        indent = len(line) - len(line.lstrip())
                        indent_str = ' ' * (indent + 4)  # Extra-Einrückung
                        replacement = f"{string[0]}\" +\n{indent_str}\"{string[1:-1]}{string[-1]}"
                        line = line.replace(string, replacement)
                        lines[issue.line_num - 1] = line
                        return True

        # Versuche, bei Kommas aufzuteilen (Listen, Funktionsparameter)
        if ',' in line:
            parts = line.split(',')
            if len(parts) > 1:
                indent = len(line) - len(line.lstrip())
                indent_str = ' ' * indent
                new_lines = [parts[0] + ',']
                for part in parts[1:-1]:
                    new_lines.append(indent_str + part.strip() + ',')
                new_lines.append(indent_str + parts[-1].strip())
                lines[issue.line_num - 1] = new_lines[0] + '\n'
                for i, new_line in enumerate(new_lines[1:], start=1):
                    lines.insert(issue.line_num - 1 + i, new_line + '\n')
                return True

        return False

    def fix_bad_variable_name(self, issue: PylintIssue) -> bool:
        """Korrigiert schlechte Variablennamen (C0103)."""
        if "Variable name" not in issue.message or "doesn't match" not in issue.message:
            return False

        match = re.search(r"Variable name \"(\w+)\"", issue.message)
        if not match:
            return False

        bad_name = match.group(1)

        lines = self.load_file(issue.file_path)
        line = lines[issue.line_num - 1]

        # Variablennamen in snake_case umwandeln
        if bad_name[0].isupper() or any(c.isupper() for c in bad_name[1:]):
            # camelCase oder PascalCase zu snake_case
            snake_name = ''.join(['_' + c.lower() if c.isupper() else c for c in bad_name])
            snake_name = snake_name.lstrip('_')

            # Ersetze nur die Variablendeklaration, nicht alle Vorkommen
            if re.search(rf"\b{bad_name}\s*=", line):
                lines[issue.line_num - 1] = line.replace(bad_name, snake_name)
                return True

        # Zu kurze Variablennamen verbessern (i, x, etc.)
        if len(bad_name) == 1 and bad_name not in ['i', 'j', 'k', 'x', 'y', 'z']:
            # Versuche, einen besseren Namen aus dem Kontext abzuleiten
            # Für dieses Beispiel verwenden wir einfach "var_"+bad_name
            better_name = f"var_{bad_name}"
            if re.search(rf"\b{bad_name}\s*=", line):
                lines[issue.line_num - 1] = line.replace(bad_name, better_name)
                return True

        return False

    def fix_similar_lines(self, issue: PylintIssue) -> bool:
        """Behandelt ähnliche Codezeilen in verschiedenen Dateien (R0801)."""
        if "Similar lines" not in issue.message:
            return False

        # Analysiere die Warnung, um die betroffenen Dateien zu identifizieren
        match = re.search(r"Similar lines in (\d+) files", issue.message)
        if not match:
            return False

        # Diese Warnung erfordert manuelle Überprüfung und Refactoring
        # Erstellen wir eine TODO-Notiz im Code

        lines = self.load_file(issue.file_path)

        # Füge einen Kommentar am Anfang der Datei ein
        todo_comment = (
            "# TODO: Dieses Modul enthält Code, der in anderen Dateien dupliziert ist.\n"
            "# Pylint-Warnung: R0801 - Similar lines in multiple files\n"
            "# Empfehlung: Gemeinsamen Code in eine separate Hilfsklasse oder Modul extrahieren.\n"
        )

        # Prüfen, ob der Kommentar bereits vorhanden ist
        if not any("" +
            "TODO: Dieses Modul enthält Code, der in anderen Dateien dupliziert ist" in line for line in lines[:5]):
            lines.insert(0, todo_comment)
            return True

        return False

    def fix_issues(self) -> int:
        """Behebe alle gefundenen Issues und gib die Anzahl der behobenen Probleme zurück."""
        # Gruppiere die Issues nach Datei,
        um mehrere Änderungen an derselben Datei effizient zu verarbeiten
        issues_by_file: Dict[str, List[PylintIssue]] = {}
        for issue in self.issues:
            if issue.file_path not in issues_by_file:
                issues_by_file[issue.file_path] = []
            issues_by_file[issue.file_path].append(issue)

        # Behandle R0801 (ähnliche Zeilen) zuerst separat,
        # da wir nur eine Markierung pro Datei hinzufügen wollen
        r0801_processed_files: Set[str] = set()

        # Verarbeite alle Issues
        for issue in self.issues:
            fixed = False
            
            # Wähle den passenden Fixer basierend auf dem pylint-Code
            if issue.code == "W0611":  # Unused import
                fixed = self.fix_unused_import(issue)
            elif issue.code == "C0303":  # Trailing whitespace
                fixed = self.fix_trailing_whitespace(issue)
            elif issue.code in ["C0111", "C0112", "C0103"]:  # Missing docstring or bad name
                if "docstring" in issue.message.lower():
                    fixed = self.fix_missing_docstring(issue)
                elif "name" in issue.message.lower():
                    fixed = self.fix_bad_variable_name(issue)
            elif issue.code == "C0301":  # Line too long
                fixed = self.fix_line_too_long(issue)
            elif issue.code == "R0801" and issue.file_path not in r0801_processed_files:  # Similar lines
                fixed = self.fix_similar_lines(issue)
                if fixed:
                    r0801_processed_files.add(issue.file_path)
            
            if fixed:
                self.fixes_applied += 1
                self.fixed_issues.append(issue)
                self.logger.info("Behoben: %sissue")
            else:
                self.skipped_issues += 1
                self.unfixed_issues.append(issue)
                self.logger.info(f"Nicht behoben: {issue}")

        # Speichere alle geänderten Dateien
        for file_path in self.file_cache:
            self.save_file(file_path)
            
        # Erstelle eine Zusammenfassung
        self.logger.info("\n" + "="*50)
        self.logger.info("ZUSAMMENFASSUNG:")
        self.logger.info("Insgesamt verarbeitet: %slen(self.issues) Probleme")
        self.logger.info("Behoben: %sself.fixes_applied Probleme")
        self.logger.info(f"Übersprungen: {self.skipped_issues} Probleme")
        
        # Gruppiere unfixed Issues nach Code für bessere Übersicht
        unfixed_by_code: Dict[str, int] = {}
        for issue in self.unfixed_issues:
            if issue.code not in unfixed_by_code:
                unfixed_by_code[issue.code] = 0
            unfixed_by_code[issue.code] += 1
            
        if unfixed_by_code:
            self.logger.info("\nNicht behobene Probleme nach Typ:")
            for code, count in sorted(unfixed_by_code.items(), key=lambda x: x[1], reverse=True):
                self.logger.info(f"  {code}: {count} Probleme")
        
        return self.fixes_applied


def parse_pylint_log(log_path: str) -> List[PylintIssue]:
    """Analysiert die pylint-Log-Datei und extrahiert die Probleme."""
    issues = []
    
    with open(log_path, 'r', encoding='utf-8') as file:
        for line in file:
            # Typisches pylint-Format: file.py:42:0: C0111: Missing docstring (missing-docstring)
            match = re.match(r'^([\w\./]+):(\d+)(?::\d+)?: ([CRWE]\d{4}): (.+?)(?:\s\([\w-]+\))?$', line.strip())
            if match:
                file_path, line_num, code, message = match.groups()
                issues.append(PylintIssue(
                    file_path=file_path,
                    line_num=int(line_num),
                    code=code,
                    message=message
                ))
    
    return issues


def main():
    """Hauptfunktion des Programms."""
    parser = argparse.ArgumentParser(description='Behebt pylint-Probleme automatisch.')
    parser.add_argument('log_file', help='" +
        "Pfad zur pylint-Log-Datei (optimization.log)')
    parser.add_argument('--dry-run', action='store_true', help='Zeigt Änderungen ohne sie anzuwenden')
    parser.add_argument('--output-log', help='Pfad zur Ausgabe-Log-Datei (optimization_fixed.log)',
                      default='optimization_fixed.log')
    parser.add_argument('--create-patch', action='store_true', 
                      help='Erstellt eine Patch-Datei mit allen Änderungen')
    args = parser.parse_args()
    
    if not os.path.exists(args.log_file):
        print(f"Fehler: Die Datei {args.log_file} existiert nicht.")
        sys.exit(1)
    
    print(f"Analysiere {args.log_file}...")
    issues = parse_pylint_log(args.log_file)
    print(f"{len(issues)} Probleme gefunden.")
    
    # Konfiguriere Logging
    log_file = args.output_log if not args.dry_run else None
    
    # Erstelle und führe den CodeFixer aus
    fixer = CodeFixer(issues, dry_run=args.dry_run, log_file=log_file)
    fixes = fixer.fix_issues()

    # Erstelle eine Patch-Datei, wenn gewünscht
    if args.create_patch and not args.dry_run and fixes > 0:
        create_patch_file(fixer.file_cache, "patch")
        print(f"Patch-Datei erstellt: patch")
    
    mode = "Testmodus" if args.dry_run else "Angewendet"
    print(f"\n{mode}: {fixes} von {len(issues)} Problemen behoben.")
    
    if not args.dry_run:
        print(f"Detailliertes Log geschrieben nach: {args.output_log}")
    
    return 0


def create_patch_file(file_cache: Dict[str, List[str]], patch_file: str):
    """Erstellt eine Patch-Datei mit allen Änderungen."""
    import difflib
    import time
    
    with open(patch_file, 'w', encoding='utf-8') as f:
        f.write(f"# Erstellt von pylint_patcher.py am {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for file_path, lines in file_cache.items():
            try:
                # Lade die Originaldatei
                with open(file_path, 'r', encoding='utf-8') as original_file:
                    original_lines = original_file.readlines()
                
                # Erstelle die Diff
                diff = difflib.unified_diff(
                    original_lines, 
                    lines,
                    fromfile=f"a/{file_path}",
                    tofile=f"b/{file_path}",
                    n=3
                )
                
                # Schreibe die Diff in die Patch-Datei
                diff_content = ''.join(diff)
                if diff_content:
                    f.write(diff_content)
                    f.write('\n')
            except Exception as e:
                f.write(f"# Fehler beim Erstellen des Patches für {file_path}: {str(e)}\n\n")


if __name__ == "__main__":
    sys.exit(main())
