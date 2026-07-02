#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-.}"

count_loc() {
  local dir="$1"

  if [[ ! -d "$REPO/$dir" ]]; then
    echo "0"
    return
  fi

  find "$REPO/$dir" -type f \
    ! -path '*/.git/*' \
    ! -path '*/node_modules/*' \
    ! -path '*/dist/*' \
    ! -path '*/build/*' \
    -print0 |
    xargs -0 awk 'END { print NR + 0 }'
}

printf "%-10s %s\n" "Folder" "LOC"
printf "%-10s %s\n" "------" "---"
printf "%-10s %s\n" "src/"  "$(count_loc src)"
printf "%-10s %s\n" "test/" "$(count_loc test)"
printf "%-10s %s\n" "docs/" "$(count_loc docs)"