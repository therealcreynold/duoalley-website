#!/usr/bin/env bash
# Copies the game's store screenshots onto this site, from the pictures the game has COMMITTED.
#
#     scripts/make-shots.sh                      uses ../duoalley
#     scripts/make-shots.sh /path/to/game/repo   uses <that>
#
# The home page shows three of the store's own framed screenshots (the game's
# marketing/screenshots-framed/, made by its Scripts/capture-screenshots.sh and
# Scripts/compose-screenshots.mjs from scripted showcase launches), so the site never shows a picture of
# the game that the App Store does not: the laptop pose's 100, the closed phone on its outside screen,
# and a phone without a fold. They are scaled down and saved as JPEG (no alpha, a tenth of the bytes) to
# assets/shots/, and scripts/shot-source.txt records the SHA-256 of each source file, so
# scripts/lint-site.py fails while the game's committed screenshots differ from what the site shows.
# After the game recaptures, run this, look at the pictures, and commit them with the record.
#
# It refuses while a source picture has uncommitted changes in the game repository, as make-icons.sh
# does for the icon: the site shows only what the game has committed.
set -euo pipefail

SITE="$(cd "$(dirname "$0")/.." && pwd)"
GAME="$(cd "${1:-$SITE/../duoalley}" && pwd)" || { echo "make-shots: no game repository there"; exit 1; }
git -C "$GAME" rev-parse --git-dir >/dev/null 2>&1 || { echo "make-shots: $GAME is not a git repository"; exit 1; }

# published name : source in the game repository : width on the page
SHOTS=(
    "hundred.jpg:marketing/screenshots-framed/duo-inner/duo-inner-02-hundred.png:640"
    "closed.jpg:marketing/screenshots-framed/duo-cover/duo-cover-01-hero.png:560"
    "phone.jpg:marketing/screenshots-framed/iphone/iphone-01-hero.png:400"
)

mkdir -p "$SITE/assets/shots"
record="$SITE/scripts/shot-source.txt"
{
    echo "# The game's framed store screenshots these pictures were made from (scripts/make-shots.sh)."
    echo "# scripts/lint-site.py fails when the game repository's committed files no longer match."
} > "$record.new"
for entry in "${SHOTS[@]}"; do
    IFS=: read -r name source width <<<"$entry"
    [ -f "$GAME/$source" ] || { rm -f "$record.new"; echo "make-shots: no $source in $GAME"; exit 1; }
    dirty="$(git -C "$GAME" status --porcelain -- "$source")"
    [ -z "$dirty" ] || { rm -f "$record.new"; echo "make-shots: $source has uncommitted changes in $GAME; commit them first"; exit 1; }
    sips --resampleWidth "$width" -s format jpeg -s formatOptions 82 "$GAME/$source" --out "$SITE/assets/shots/$name" >/dev/null
    dims="$(sips -g pixelWidth -g pixelHeight "$SITE/assets/shots/$name" | awk '/pixel(Width|Height)/ {printf "%s ", $2}')"
    echo "  assets/shots/$name  $dims(from $source)"
    (cd "$GAME" && shasum -a 256 "$source") >> "$record.new"
done
mv "$record.new" "$record"
echo "make-shots: wrote ${#SHOTS[@]} pictures and scripts/shot-source.txt from $GAME at $(git -C "$GAME" rev-parse --short HEAD)"
echo "NOW LOOK AT THEM, and set each <img>'s width and height in index.html to the sizes above (the lint checks)."
