#!/usr/bin/env bash
set -euo pipefail
trap 'echo "bug: stage-hunk crashed unexpectedly — please report this" >&2' ERR

# Stage or unstage specific hunks from a git diff without interactive
# prompts. Takes a file and one or more hunk indices (as shown by
# --list-hunks), and applies them to the index. Does not commit.
#
# Usage:
#   stage-hunk.sh <file> <N> [N ...]
#   stage-hunk.sh --unstage <file> <N> [N ...]
#   stage-hunk.sh --list-hunks [--staged] <file>
#
# Examples:
#   stage-hunk.sh src/pets.md 2
#   stage-hunk.sh src/pets.md 1 3 5
#   stage-hunk.sh --unstage src/pets.md 1
#   stage-hunk.sh --list-hunks src/pets.md
#   stage-hunk.sh --list-hunks --staged src/pets.md

UNSTAGE=0

usage() {
  echo "Usage: $0 <file> <N> [N ...]" >&2
  echo "       $0 --unstage <file> <N> [N ...]" >&2
  echo "       $0 --list-hunks [--staged] <file>" >&2
  exit 1
}

# --- List hunks mode ---
if [[ "${1:-}" == "--list-hunks" ]]; then
  shift
  LIST_STAGED=0
  if [[ "${1:-}" == "--staged" ]]; then
    LIST_STAGED=1
    shift
  fi
  [[ $# -ne 1 ]] && usage
  FILE="$1"
  # Use -U0 to split into finest-grained hunks
  if [[ $LIST_STAGED -eq 1 ]]; then
    DIFF=$(git diff -U0 --cached -- "$FILE")
  else
    DIFF=$(git diff -U0 -- "$FILE")
  fi
  if [[ -z "$DIFF" ]]; then
    if [[ $LIST_STAGED -eq 1 ]]; then
      echo "error: no staged changes in $FILE" >&2
    else
      echo "error: no unstaged changes in $FILE" >&2
    fi
    exit 1
  fi

  hunk_idx=0
  adds=0; dels=0; preview=""
  new_start=0; new_count=0

  print_hunk() {
    [[ $hunk_idx -eq 0 ]] && return
    new_end=$(( new_start + new_count - 1 ))
    local total=$(( dels + adds ))
    [[ ${#preview} -gt 80 ]] && preview="${preview:0:77}..."
    printf "hunk %d: lines %-8s (%d del, %d add, %d lines) %s\n" \
      "$hunk_idx" "${new_start}-${new_end}" "$dels" "$adds" "$total" "\"${preview}\""
  }

  while IFS= read -r line; do
    if [[ "$line" =~ ^@@\ -([0-9]+)(,([0-9]+))?\ \+([0-9]+)(,([0-9]+))?\ @@ ]]; then
      print_hunk
      ((hunk_idx++)) || true
      new_start="${BASH_REMATCH[4]}"
      new_count="${BASH_REMATCH[6]:-1}"
      adds=0; dels=0; preview=""
      continue
    fi
    case "${line:0:1}" in
      "+") ((adds++)) || true
           [[ -z "$preview" ]] && preview="${line:1}" ;;
      "-") ((dels++)) || true
           [[ -z "$preview" && $adds -eq 0 ]] && preview="${line:1}" ;;
    esac
  done <<< "$DIFF"
  print_hunk
  exit 0
fi

# --- Stage/unstage mode ---
if [[ "${1:-}" == "--unstage" ]]; then
  UNSTAGE=1
  shift
fi

[[ $# -lt 2 ]] && usage

FILE="$1"; shift

# Remaining args are hunk indices (plain integers, 1-based, as shown by --list-hunks)
declare -A wanted_hunks
for arg in "$@"; do
  if [[ "$arg" =~ ^[0-9]+$ ]]; then
    wanted_hunks["$arg"]=1
  else
    echo "error: expected hunk index (integer), got: $arg" >&2
    usage
  fi
done

# Get the appropriate diff
if [[ $UNSTAGE -eq 1 ]]; then
  DIFF=$(git diff --cached -- "$FILE")
  if [[ -z "$DIFF" ]]; then
    echo "error: no staged changes in $FILE" >&2
    exit 1
  fi
else
  DIFF=$(git diff -- "$FILE")
  if [[ -z "$DIFF" ]]; then
    echo "error: no unstaged changes in $FILE" >&2
    exit 1
  fi
fi

# Resolve hunk indices to line ranges using U0 diff (matches --list-hunks numbering)
if [[ $UNSTAGE -eq 1 ]]; then
  DIFF_U0=$(git diff -U0 --cached -- "$FILE")
else
  DIFF_U0=$(git diff -U0 -- "$FILE")
fi
hunk_idx=0
resolved_ranges=()
while IFS= read -r line; do
  if [[ "$line" =~ ^@@\ -([0-9]+)(,([0-9]+))?\ \+([0-9]+)(,([0-9]+))?\ @@ ]]; then
    ((hunk_idx++)) || true
    if [[ -n "${wanted_hunks[$hunk_idx]:-}" ]]; then
      new_start="${BASH_REMATCH[4]}"
      new_count="${BASH_REMATCH[6]:-1}"
      new_end=$(( new_start + new_count - 1 ))
      resolved_ranges+=("${new_start}-${new_end}")
    fi
  fi
done <<< "$DIFF_U0"

if [[ ${#resolved_ranges[@]} -eq 0 ]]; then
  echo "error: no hunks matched indices $* (file has $hunk_idx hunks)" >&2
  exit 1
fi

LINE_SPEC=$(IFS=','; echo "${resolved_ranges[*]}")

# Parse line spec into an array of min,max pairs
parse_ranges() {
  local spec="$1"
  local IFS=','
  for part in $spec; do
    if [[ "$part" =~ ^([0-9]+)-([0-9]+)$ ]]; then
      echo "${BASH_REMATCH[1]} ${BASH_REMATCH[2]}"
    elif [[ "$part" =~ ^([0-9]+)$ ]]; then
      echo "${BASH_REMATCH[1]} ${BASH_REMATCH[1]}"
    else
      echo "error: invalid line spec: $part" >&2
      exit 1
    fi
  done
}

RANGES=$(parse_ranges "$LINE_SPEC") || exit 1

# Check if a new-side line number falls within any requested range
in_range() {
  local line="$1"
  while read -r range_start range_end; do
    if [[ $line -ge $range_start && $line -le $range_end ]]; then
      return 0
    fi
  done <<< "$RANGES"
  return 1
}

# Build a filtered patch.
# Strategy: walk the diff line by line, tracking new-side line numbers.
# For each hunk, keep context lines as-is, keep deletions/additions only
# if the corresponding new-side line is in range. If a hunk has no
# selected changes after filtering, drop it entirely.
#
# HAZARD: BASH_REMATCH is global — any [[ =~ ]] in a called function
# (e.g. flush_hunk) will overwrite it. Always capture BASH_REMATCH
# values into local variables immediately after the match, before
# calling any function that might run its own regex.

build_patch() {
  local is_in_header=1
  local hunk_lines=()
  local hunk_header=""
  local old_start=0 new_start=0 new_count=0
  local current_new_line=0
  local header_lines=()

  while IFS= read -r line; do
    # Diff header lines (diff --git, index, ---, +++)
    if [[ "$is_in_header" -eq 1 ]]; then
      if [[ "$line" =~ ^@@ ]]; then
        is_in_header=0
      else
        header_lines+=("$line")
        continue
      fi
    fi

    # Start of a new hunk
    if [[ "$line" =~ ^@@\ -([0-9]+)(,([0-9]+))?\ \+([0-9]+)(,([0-9]+))?\ @@ ]]; then
      # Capture BEFORE flush_hunk — it runs a regex that clobbers BASH_REMATCH
      hunk_header="$line"
      old_start="${BASH_REMATCH[1]}"
      new_start="${BASH_REMATCH[4]}"
      new_count="${BASH_REMATCH[6]:-1}"

      # Flush previous hunk if it had selected changes
      if [[ ${#hunk_lines[@]} -gt 0 ]]; then
        flush_hunk
      fi

      hunk_lines=()
      current_new_line=$new_start
      continue
    fi

    # Track lines within a hunk
    case "${line:0:1}" in
      " ")
        hunk_lines+=("ctx|$current_new_line|$line")
        ((current_new_line++)) || true
        ;;
      "+")
        hunk_lines+=("add|$current_new_line|$line")
        ((current_new_line++)) || true
        ;;
      "-")
        hunk_lines+=("del|$current_new_line|$line")
        ;;
      *)
        # "\ No newline at end of file" or similar
        hunk_lines+=("meta|$current_new_line|$line")
        ;;
    esac
  done <<< "$DIFF"

  # Flush last hunk
  if [[ ${#hunk_lines[@]} -gt 0 ]]; then
    flush_hunk
  fi
}

IS_HEADER_PRINTED=0
# Track cumulative new-side offset from dropped additions / kept deletions
# so subsequent hunk headers stay accurate.
NEW_OFFSET=0

flush_hunk() {
  # Filter: keep context, keep del/add only if in range
  local filtered=()
  local has_selected_changes=0
  local is_previous_line_kept=1

  for entry in "${hunk_lines[@]}"; do
    local type="${entry%%|*}"
    local rest="${entry#*|}"
    local line_number="${rest%%|*}"
    local content="${rest#*|}"

    case "$type" in
      ctx)
        filtered+=("$content")
        is_previous_line_kept=1
        ;;
      add)
        if in_range "$line_number"; then
          filtered+=("$content")
          has_selected_changes=1
          is_previous_line_kept=1
        else
          if [[ $UNSTAGE -eq 1 ]]; then
            # Unstage: out-of-range addition exists in the index, keep as context
            filtered+=(" ${content:1}")
            is_previous_line_kept=1
          else
            # Stage: out-of-range addition doesn't exist in the index, drop it
            is_previous_line_kept=0
          fi
        fi
        ;;
      del)
        if in_range "$line_number"; then
          filtered+=("$content")
          has_selected_changes=1
          is_previous_line_kept=1
        else
          if [[ $UNSTAGE -eq 1 ]]; then
            # Unstage: out-of-range deletion's old content isn't in the index, drop it
            is_previous_line_kept=0
          else
            # Stage: out-of-range deletion's old content is in the index, keep as context
            filtered+=(" ${content:1}")
            is_previous_line_kept=1
          fi
        fi
        ;;
      meta)
        # "\ No newline at end of file" — only emit if the preceding
        # line was kept, otherwise it attaches to the wrong line.
        if [[ $is_previous_line_kept -eq 1 ]]; then
          filtered+=("$content")
        fi
        ;;
    esac
  done

  # Recalculate hunk header counts
  local old_side_count=0 new_side_count=0
  for line in "${filtered[@]}"; do
    case "${line:0:1}" in
      " ") ((old_side_count++)) || true; ((new_side_count++)) || true ;;
      "-") ((old_side_count++)) || true ;;
      "+") ((new_side_count++)) || true ;;
    esac
  done

  # Update cumulative offset: difference between filtered new-side and
  # original new_count tells us how many lines were dropped/added.
  NEW_OFFSET=$(( NEW_OFFSET + new_side_count - new_count ))

  if [[ $has_selected_changes -eq 0 ]]; then
    return
  fi

  # Print header once
  if [[ $IS_HEADER_PRINTED -eq 0 ]]; then
    for header_line in "${header_lines[@]}"; do
      echo "$header_line"
    done
    IS_HEADER_PRINTED=1
  fi

  # Extract any function context from original @@ line
  local function_context=""
  if [[ "$hunk_header" =~ @@.*@@(.*) ]]; then
    function_context="${BASH_REMATCH[1]}"
  fi

  # Adjust new_start by cumulative offset from previous hunks
  local adjusted_new_start=$(( new_start + NEW_OFFSET - (new_side_count - new_count) ))
  echo "@@ -${old_start},${old_side_count} +${adjusted_new_start},${new_side_count} @@${function_context}"
  for line in "${filtered[@]}"; do
    echo "$line"
  done
}

PATCH=$(build_patch)

if [[ -z "$PATCH" ]]; then
  echo "error: no hunks matched indices $* in $FILE" >&2
  exit 1
fi

# Write patch to a temp file. Use mktemp default (usually /tmp) with
# restrictive permissions so other users can't read it. The trap handles
# normal exits; the file is also owner-only in case cleanup is missed.
TMPFILE=$(mktemp)
chmod 600 "$TMPFILE"
trap 'rm -f "$TMPFILE"' EXIT
echo "$PATCH" > "$TMPFILE"

# Apply — use --check first, then apply. If strict mode fails, retry with
# whitespace tolerance. The check and apply use the same flags so behaviour
# is consistent.
apply_patch() {
  local -a flags=(--cached)
  [[ $UNSTAGE -eq 1 ]] && flags+=(--reverse)
  [[ $# -gt 0 ]] && flags+=("$1")
  git apply "${flags[@]}" --check "$TMPFILE" && \
  git apply "${flags[@]}" "$TMPFILE"
}

if ! apply_patch 2>/dev/null; then
  if ! apply_patch "--whitespace=nowarn"; then
    echo "error: generated patch failed to apply" >&2
    echo "patch content:" >&2
    cat "$TMPFILE" >&2
    exit 1
  fi
fi

if [[ $UNSTAGE -eq 1 ]]; then
  echo "unstaged hunks $* from $FILE"
else
  echo "staged hunks $* from $FILE"
fi

# Show what's staged so the caller can verify
git diff --cached --stat -- "$FILE"
