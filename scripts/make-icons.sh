#!/usr/bin/env bash
# Redraws every picture of the app icon on this site from the icon the game has COMMITTED.
#
#     scripts/make-icons.sh                      uses ../hingealley (or ../duoalley)
#     scripts/make-icons.sh /path/to/game/repo   uses <that>
#
# THE ONE COMMAND. The owner has not picked the icon yet (the game's owner-open O9: five options drawn
# by `swift run alley-art icon-options`, option 1 committed as a placeholder). Whatever the game
# repository has in app/DuoAlley/AppIcon.icon when this runs is what the site shows, so after the owner
# picks and the game commits the new AppIcon.icon, this one command brings the site into line:
#
#     scripts/make-icons.sh && python3 scripts/lint-site.py
#
# then look at the pictures and commit them with scripts/icon-source.txt. scripts/lint-site.py fails
# while the committed AppIcon.icon differs from the one recorded in scripts/icon-source.txt, so a site
# showing a retired icon cannot pass the gate while the game repository sits beside it.
#
# WHAT IT DRAWS. The game's own renderer, `swift run -c release alley-art marketing-icon`, the one that
# draws the store's marketing icon (marketing/icon/ in the game repository), so the site and the store
# can never show two drawings of one icon (the game's decision 168; until then this script drew its own
# with headless Brave). It reads icon.json and composites the light appearance's fill and layers back to
# front. Icon Composer's own glass and drop shadows are NOT drawn: what comes out is the flat artwork,
# which is what a favicon should be.
#
# The game's `node Scripts/compose-creative.mjs` runs this script after it redraws marketing/icon/, so
# that one command refreshes every copy of the icon in both repositories.
#
# Scaled with sips. Every file written is opaque (a round trip through an uncompressed BMP drops any
# alpha channel), because an apple-touch-icon with transparency is drawn on black by iOS.
#
# Writes assets/icon-{32,96,180,512}.png and scripts/icon-source.txt.
set -euo pipefail

SITE="$(cd "$(dirname "$0")/.." && pwd)"
DEFAULT_GAME="$SITE/../hingealley"; [ -d "$DEFAULT_GAME" ] || DEFAULT_GAME="$SITE/../duoalley"
GAME="$(cd "${1:-$DEFAULT_GAME}" && pwd)" || { echo "make-icons: no game repository there"; exit 1; }
ICON="$GAME/app/DuoAlley/AppIcon.icon"
[ -f "$ICON/icon.json" ] || { echo "make-icons: no $ICON/icon.json"; exit 1; }
# COMMITTED means committed: the files are read from the working tree, so refuse while it differs from
# HEAD (an edited, staged or untracked file under AppIcon.icon), or the site could show an icon nobody
# has committed. scripts/lint-site.py hashes the HEAD blobs, not the working tree, for the same reason.
git -C "$GAME" rev-parse --git-dir >/dev/null 2>&1 || { echo "make-icons: $GAME is not a git repository"; exit 1; }
dirty="$(git -C "$GAME" status --porcelain --untracked-files=all -- app/DuoAlley/AppIcon.icon)"
[ -z "$dirty" ] || { printf 'make-icons: AppIcon.icon has uncommitted changes in %s; commit them first:\n%s\n' "$GAME" "$dirty"; exit 1; }
WORK="$(mktemp -d -t duoalley-icons)"
trap 'rm -rf "$WORK"' EXIT

( cd "$GAME" && DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode-beta.app/Contents/Developer}" \
    swift run -c release alley-art marketing-icon "$WORK/drawn" --icon "$ICON" >/dev/null ) \
    || { echo "make-icons: alley-art marketing-icon failed in $GAME"; exit 1; }
cp "$WORK/drawn/app-icon-1024.png" "$WORK/full.png"
[ -s "$WORK/full.png" ] || { echo "make-icons: alley-art drew nothing"; exit 1; }

for size in 512 180 96 32; do
    sips -z "$size" "$size" "$WORK/full.png" --out "$WORK/s.png" >/dev/null
    sips -s format bmp "$WORK/s.png" --out "$WORK/s.bmp" >/dev/null
    sips -s format png "$WORK/s.bmp" --out "$SITE/assets/icon-$size.png" >/dev/null
    alpha=$(sips -g hasAlpha "$SITE/assets/icon-$size.png" | awk '/hasAlpha/ {print $2}')
    [ "$alpha" = "no" ] || { echo "make-icons: icon-$size.png still has alpha"; exit 1; }
    echo "  assets/icon-$size.png"
done

# What it was drawn from, for scripts/lint-site.py to compare with the game repository.
{
    echo "# The game's AppIcon.icon these pictures were drawn from (scripts/make-icons.sh)."
    echo "# scripts/lint-site.py fails when the game repository's files no longer match."
    (cd "$ICON" && shasum -a 256 icon.json Assets/*.png)
} > "$SITE/scripts/icon-source.txt"
echo "make-icons: wrote 4 pictures and scripts/icon-source.txt from $ICON at $(git -C "$GAME" rev-parse --short HEAD)"
