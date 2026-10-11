#!/usr/bin/env bash
# Copy a file's contents to the system clipboard, auto-detecting the tool.
set -euo pipefail

file="${1:?usage: copy-to-clipboard.sh <file>}"
[[ -r "$file" ]] || { echo "cannot read: $file" >&2; exit 1; }

if [[ -n "${WAYLAND_DISPLAY:-}" ]] && command -v wl-copy >/dev/null 2>&1; then
  tool=wl-copy
  wl-copy < "$file"
elif [[ -n "${DISPLAY:-}" ]] && command -v xclip >/dev/null 2>&1; then
  tool=xclip
  xclip -selection clipboard < "$file"
elif [[ -n "${DISPLAY:-}" ]] && command -v xsel >/dev/null 2>&1; then
  tool=xsel
  xsel --clipboard --input < "$file"
elif command -v pbcopy >/dev/null 2>&1; then
  tool=pbcopy
  pbcopy < "$file"
else
  echo "no clipboard tool found (tried wl-copy, xclip, xsel, pbcopy)" >&2
  exit 1
fi

echo "copied $(wc -c < "$file" | tr -d ' ') bytes to clipboard via $tool"
