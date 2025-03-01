#!/bin/bash
# Advanced File Browser and Search Script

# Ensure proper error handling
set -euo pipefail

# Global variables
CURRENT_DIR="$HOME/ailinux"

# Help function
show_help() {
    echo "-------------------------"
    echo "📂 File Browser Help"
    echo "-------------------------"
    echo "📌 Navigation:"
    echo "  - 'cd <directory>'     → Change directory"
    echo "  - 'cd ..'              → Go to parent directory"
    echo "  - 'ls'                 → List files and directories"
    echo ""
    echo "📌 Search:"
    echo "  - 'showpost py'        → Search for .py files"
    echo "  - 'showpost *.py --dir'  → Search .py files in current directory"
    echo "  - 'showpost py js'     → Search multiple file types"
    echo ""
    echo "📌 Extras:"
    echo "  - 'tree'               → Show directory structure"
    echo "  - 'help'               → Show this help"
    echo "  - 'exit'               → Exit the browser"
    echo "-------------------------"
}

# Safely list directory contents
safe_list() {
    local dir="${1:-$CURRENT_DIR}"
    local dirs=()
    local files=()

    # Prevent error if no files exist
    shopt -s nullglob

    # Separate directories and files
    for item in "$dir"/*; do
        if [[ -d "$item" ]]; then
            dirs+=("$(basename "$item")/")
        elif [[ -f "$item" ]]; then
            files+=("$(basename "$item")")
        fi
    done

    # Restore default shell behavior
    shopt -u nullglob

    # Stellen Sie sicher, dass kein Rautezeichen am Anfang steht
    echo "📂 Verzeichnisse und Dateien:"

    # Display directories in blue
    if [[ ${#dirs[@]} -gt 0 ]]; then
        echo "Verzeichnisse:"
        printf "\033[0;34m%s\033[0m\n" "${dirs[@]}"
    fi

    # Display files
    if [[ ${#files[@]} -gt 0 ]]; then
        echo "Dateien:"
        printf "%s\n" "${files[@]}"
    fi

    if [[ ${#dirs[@]} -eq 0 && ${#files[@]} -eq 0 ]]; then
        echo "📂 (Verzeichnis ist leer)"
    fi

    echo "-------------------------"
}

# Advanced file search function
search_files() {
    local search_terms=()
    local search_mode="subdir"
    local find_depth=()

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dir)
                search_mode="dir"
                find_depth=(-maxdepth 1)
                shift
                ;;
            --subdir)
                search_mode="subdir"
                find_depth=()
                shift
                ;;
            *)
                # Vereinfachte und robustere Mustererkennung
                local pattern="$1"
                
                # Wenn Muster bereits ein Wildcard-Muster ist (*.py), behalte es bei
                if [[ "$pattern" == \** ]]; then
                    search_terms+=("$pattern")
                # Wenn Muster nur eine Erweiterung ist (py), füge *. hinzu
                elif [[ "$pattern" != *\.* && "$pattern" != \** ]]; then
                    search_terms+=("*.$pattern")
                # Ansonsten verwende das Muster wie angegeben
                else
                    search_terms+=("$pattern")
                fi
                
                shift
                ;;
        esac
    done

    # Validate search terms
    if [[ ${#search_terms[@]} -eq 0 ]]; then
        echo "⚠️ Bitte geben Sie mindestens ein Suchmuster an!"
        return 1
    fi

    # Print debug info
    echo "🔍 Suche nach: ${search_terms[*]} in ${search_mode} Modus"

    # Construct find command - Vereinfachte Version
    local find_cmd=("find" "$CURRENT_DIR" "${find_depth[@]}" "-type" "f")
    
    # Füge -name Argumente hinzu
    if [[ ${#search_terms[@]} -gt 0 ]]; then
        find_cmd+=("(")
        local first=true
        for term in "${search_terms[@]}"; do
            if $first; then
                find_cmd+=("-name" "$term")
                first=false
            else
                find_cmd+=("-o" "-name" "$term")
            fi
        done
        find_cmd+=(")")
    fi
    
    # Füge Ausschlüsse hinzu
    find_cmd+=("-not" "-path" "*/node_modules/*" 
               "-not" "-path" "*/dist/*" 
               "-not" "-path" "*/build/*" 
               "-not" "-path" "*/__pycache__/*")
    
    # Debug: Zeige den Befehl
    echo "🔍 Befehl: ${find_cmd[*]}"
    
    # Execute find - sicheres Handling
    echo "🔎 Durchsuche $CURRENT_DIR..."
    local results=()
    
    # Führe den Befehl aus und erfasse Fehler
    if find_output=$("${find_cmd[@]}" 2>/dev/null); then
        
        # Lese Ergebnisse in Array ein
        while IFS= read -r line; do
            [[ -n "$line" ]] && results+=("$line")
        done <<< "$find_output"
    else
        echo "⚠️ Suchfehler aufgetreten."
        return 1
    fi

    # Check results
    if [[ ${#results[@]} -eq 0 ]]; then
        echo "❌ Keine Dateien gefunden, die dem Muster entsprechen."
        return 0
    fi

    echo "✅ ${#results[@]} Dateien gefunden."

    # Display results with path and contents
    for file in "${results[@]}"; do
        # Display full path in green
        echo -e "\n\033[0;32m📂 Pfad: $file\033[0m"
        
        # Display file contents
        echo "----------------"
        cat "$file"
        echo "----------------"
    done
    
    return 0
}

# Change directory function
change_directory() {
    local target_dir="$1"
    local new_path

    # Entferne mögliche Rautezeichen am Anfang
    target_dir="${target_dir#\#}"

    # Handle special directory cases
    case "$target_dir" in
        "..") new_path=$(dirname "$CURRENT_DIR") ;;
        "~") new_path="$HOME" ;;
        /*) new_path="$target_dir" ;;
        *) new_path="$CURRENT_DIR/$target_dir" ;;
    esac

    # Validate and change directory
    if [[ -d "$new_path" ]]; then
        CURRENT_DIR=$(realpath "$new_path")
        echo "-------------------------"
        echo "📂 Gewechselt zu: $CURRENT_DIR"
        safe_list
    else
        echo "❌ Ordner nicht gefunden: $target_dir"
    fi
}

# Show directory structure
show_directory_tree() {
    echo "📂 Verzeichnisstruktur von $CURRENT_DIR:"
    if command -v tree &> /dev/null; then
        tree "$CURRENT_DIR" --dirsfirst --noreport \
            -I "node_modules|dist|build|__pycache__"
    else
        echo "❌ 'tree'-Befehl nicht gefunden. Bitte installieren Sie das 'tree'-Paket."
        find "$CURRENT_DIR" -type d -not -path "*/node_modules/*" -not -path "*/dist/*" -not -path "*/build/*" -not -path "*/__pycache__/*" | sort
    fi
    echo "-------------------------"
}

# Interactive file browser
interactive_browser() {
    # Initial directory listing
    echo "-------------------------"
    echo "📂 Aktuelles Verzeichnis: $CURRENT_DIR"
    echo "-------------------------"
    safe_list

    while true; do
        echo "💡 Verfügbare Befehle: 'cd <Ordner>', 'cd ..', 'ls', 'showpost <Suchmuster> --dir/--subdir', 'tree', 'help', 'exit'"
        echo "🔎 Beispiel für Suche: 'showpost py --dir'"
        echo "-------------------------"

        read -p "$(whoami)@$(basename "$CURRENT_DIR")$ " -r input
        echo "-------------------------"
        
        # Prüfe, ob Eingabe leer ist
        if [[ -z "$input" ]]; then
            continue
        fi
        
        # Entferne mögliche Rautezeichen am Anfang der Eingabe
        input="${input#\#}"
        
        # Split input into command and arguments
        read -ra cmd_args <<< "$input"

        case "${cmd_args[0]}" in
            exit) 
                echo "Beende das Skript. Auf Wiedersehen!"
                return 0 
                ;;
            help) 
                show_help 
                ;;
            ls) 
                safe_list 
                ;;
            tree) 
                show_directory_tree 
                ;;
            cd)
                if [[ ${#cmd_args[@]} -lt 2 ]]; then
                    echo "⚠️ Bitte geben Sie ein Verzeichnis an."
                else
                    change_directory "${cmd_args[1]}"
                fi
                ;;
            showpost) 
                if [[ ${#cmd_args[@]} -lt 2 ]]; then
                    echo "⚠️ Bitte geben Sie mindestens ein Suchmuster an."
                else
                    # Ausführung mit Fehlerbehandlung
                    if ! search_files "${cmd_args[@]:1}"; then
                        echo "⚠️ Die Suche wurde mit Fehlern abgeschlossen."
                    fi
                fi
                ;;
            *) 
                echo "❌ Unbekannter Befehl '${cmd_args[0]}'. Geben Sie 'help' für eine Liste der Befehle ein." 
                ;;
        esac
    done
}

# Main menu function
main_menu() {
    while true; do
        echo "📂 Datei-Browser und Analyse"
        echo "1) Interaktiver Datei-Browser"
        echo "2) Verzeichnisstruktur anzeigen"
        echo "3) Beenden"
        read -p "Bitte wählen Sie eine Option (1-3): " choice
        case "$choice" in
            1) interactive_browser ;;
            2) 
                CURRENT_DIR="$HOME/ailinux"
                show_directory_tree 
                ;;
            3) exit 0 ;;
            *) echo "Ungültige Option. Bitte wählen Sie 1, 2 oder 3." ;;
        esac
    done
}

# Trap für ordnungsgemäße Beendigung
trap 'echo "Skript wird beendet..."; exit 0' SIGINT SIGTERM

# Start the script
main_menu
