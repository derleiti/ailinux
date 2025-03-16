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
from typing import Dict, List, Tuple, Optional


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

    def __init__(self, issues: List[PylintIssue], dry_run: bool = False):
        self.issues = issues
        self.dry_run = dry_run
        self.file_cache: Dict[str, List[str]] = {}
        self.fixes_applied = 0

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

    def fix_issues(self) -> int:
        """Behebe alle gefundenen Issues und gib die Anzahl der behobenen Probleme zurück."""
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

            if fixed:
                self.fixes_applied += 1
                print(f"Behoben: {issue}")
            else:
                print(f"Nicht behoben: {issue}")

        # Speichere alle geänderten Dateien
        for file_path in self.file_cache:
            self.save_file(file_path)

        return self.fixes_applied


def parse_pylint_log(log_path: str) -> List[PylintIssue]:
    """Analysiert die pylint-Log-Datei und extrahiert die Probleme."""
    issues = []

    with open(log_path, 'r', encoding='utf-8') as file:
        for line in file:
            # Typisches pylint-Format: file.py:42:0: C0111: Missing docstring (missing-docstring)
            match = re.match(r'" +
                "^([\w\./]+):(\d+)(?::\d+)?: ([CRWE]\d{4}): (.+?)(?:\s\([\w-]+\))?$', line.strip())
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
    parser.add_argument('log_file', help='Pfad zur pylint-Log-Datei (optimization.log)')
    parser.add_argument('--dry-run', action='store_true', help='" +
        "Zeigt Änderungen ohne sie anzuwenden')
    args = parser.parse_args()

    if not os.path.exists(args.log_file):
        print(f"Fehler: Die Datei {args.log_file} existiert nicht.")
        sys.exit(1)

    print(f"Analysiere {args.log_file}...")
    issues = parse_pylint_log(args.log_file)
    print(f"{len(issues)} Probleme gefunden.")

    fixer = CodeFixer(issues, dry_run=args.dry_run)
    fixes = fixer.fix_issues()

    mode = "Testmodus" if args.dry_run else "Angewendet"
    print(f"\n{mode}: {fixes} von {len(issues)} Problemen behoben.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
