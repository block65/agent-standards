#!/usr/bin/env bash
set -euo pipefail

# Builds a repo whose committed state is clean, so every check in the eval suite
# fires on the working-tree change the test makes rather than on the fixture.
# Usage: setup-test-repo.sh <dir>

DIR="${1:?usage: setup-test-repo.sh <dir>}"

rm -rf "$DIR"
mkdir -p "$DIR/src" "$DIR/infra"
cd "$DIR"

git init -q .
git config user.email test@example.com
git config user.name "Test"
git config commit.gpgsign false

cat > src/ingest.ts <<'EOF'
export function ingest(rows: string[]) {
  console.log("spam", rows.length);
  const seen = new Set<string>();
  return rows.filter((r) => !seen.has(r));
}
EOF

cat > src/store.ts <<'EOF'
export function liveQuery() {
  return "SELECT id FROM review WHERE state = 'open'";
}
EOF

cat > infra/boot.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo "booting"
EOF

git add -A
git commit -qm "base"
