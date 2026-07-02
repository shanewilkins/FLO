#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-.}"

count_loc() {
  local dir="$1"

  if [[ ! -d "$REPO/$dir" ]]; then
    echo 0
    return
  fi

  find "$REPO/$dir" -type f \( -name '*.py' -o -name '*.md' \) -print0 |
    while IFS= read -r -d '' file; do
      wc -l < "$file"
    done |
    awk '{ total += $1 } END { print total + 0 }'
}

printf "%-10s %s\n" "Folder" "LOC"
printf "%-10s %s\n" "------" "---"
printf "%-10s %s\n" "src/"  "$(count_loc src)"
printf "%-10s %s\n" "tests/" "$(count_loc tests)"
printf "%-10s %s\n" "docs/" "$(count_loc docs)"