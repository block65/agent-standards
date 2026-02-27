#!/usr/bin/env bash
set -euo pipefail

# Creates a test git repo with known dirty state for stage-hunk eval.
# Usage: setup-test-repo.sh <target-dir>

DIR="${1:?usage: setup-test-repo.sh <target-dir>}"

rm -rf "$DIR"
mkdir -p "$DIR/src"
cd "$DIR"

git init
git config user.email "test@test.com"
git config user.name "Test"

# Committed state
cat > src/pets.md << 'EOF'
# Favourite Pets

## Dogs

Friendly and loyal.

## Cats

Independent and curious.

## Fish

Calming to watch.
EOF

cat > src/snacks.md << 'EOF'
# Best Snacks

## Kaya Toast

Sweet coconut jam on crispy bread.

## Satay

Grilled skewers with peanut sauce.

## Mango Sticky Rice

Sweet mango with coconut sticky rice.
EOF

cat > src/potions.md << 'EOF'
# Potion Recipes

## Sleepy Soup

Knocks out a dragon for 8 hours.

- 3 cups of moon water
- 1 enchanted turnip

## Giggle Juice

Makes goblins laugh uncontrollably.

- 2 ticklish feathers
- 1 jar of pixie dust

## Shrinking Syrup

Reduces ogres to hamster size.

- 5 tiny mushrooms
- 1 wizard sneeze

## Glow Goo

Makes anything glow in the dark.

- 4 firefly tears
- 1 haunted lantern
EOF

git add -A
git commit -m "test fixtures"

# Dirty state — 3 hunks per file
cat > src/pets.md << 'EOF'
# Favourite Pets

## Dogs

Friendly, loyal, and love walking by the canal.

## Cats

Independent and curious.

## Tokay Gecko

Loud but eats the mosquitoes.

## Fish

Calming to watch, especially koi.
EOF

cat > src/snacks.md << 'EOF'
# Best Snacks

## Kaya Toast

Sweet coconut jam on crispy bread. Best from Ya Kun.

## Satay

Grilled skewers with peanut sauce.

## Roti Canai

Flaky flatbread with dhal.

## Mango Sticky Rice

Sweet mango with coconut sticky rice. Use Nam Dok Mai mangoes.
EOF

cat > src/potions.md << 'EOF'
# Potion Recipes

## Sleepy Soup

Knocks out a dragon for 12 hours.

- 3 cups of moon water
- 1 enchanted turnip

## Giggle Juice

Makes goblins laugh uncontrollably.

- 2 ticklish feathers
- 1 bucket of pixie dust

## Shrinking Syrup

Reduces ogres to hamster size.

- 5 tiny mushrooms
- 1 wizard sneeze
- A pinch of fairy salt

## Glow Goo

Makes anything glow in the dark.

- 4 firefly tears
- 1 haunted lantern
EOF

echo "Test repo ready at $DIR"
echo ""
echo "pets.md hunks:"
echo "  line 5:     Dogs description changed"
echo "  lines 11-14: Tokay Gecko section added"
echo "  line 17:    Fish description changed"
echo ""
echo "snacks.md hunks:"
echo "  line 5:     Kaya Toast description changed"
echo "  lines 11-14: Roti Canai section added"
echo "  line 17:    Mango Sticky Rice description changed"
echo ""
echo "potions.md hunks (widely spaced — separate @@ blocks):"
echo "  line 5:     Sleepy Soup duration changed"
echo "  line 15:    Giggle Juice amount changed"
echo "  line 26:    Shrinking Syrup fairy salt added"
