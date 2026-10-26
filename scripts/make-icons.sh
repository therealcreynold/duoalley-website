#!/usr/bin/env bash
# Redraws every picture of the app icon on this site from the icon the game has COMMITTED.
#
#     scripts/make-icons.sh                      uses ../duoalley
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
# WHAT IT DRAWS. The icon is an Icon Composer document: full-frame 1024 x 1024 layers (backdrop,
# plate, ramp, ball, listed top first in icon.json) over a solid fill. Here the light appearance's
# layers are stacked bottom first on that fill, at full frame, exactly as icon.json lists them. Icon
# Composer's own glass and drop shadows are NOT drawn: what comes out is the flat artwork, which is what
# a favicon should be. The fill colour is read from icon.json, never typed here.
#
# Drawn by headless Brave from local files only (nothing is fetched), then scaled with sips. Every file
# written is opaque (a round trip through an uncompressed BMP drops the alpha channel), because an
# apple-touch-icon with transparency is drawn on black by iOS.
#
# Writes assets/icon-{32,96,180,512}.png and scripts/icon-source.txt.
set -euo pipefail

SITE="$(cd "$(dirname "$0")/.." && pwd)"
GAME="$(cd "${1:-$SITE/../duoalley}" && pwd)" || { echo "make-icons: no game repository there"; exit 1; }
ICON="$GAME/app/DuoAlley/AppIcon.icon"
[ -f "$ICON/icon.json" ] || { echo "make-icons: no $ICON/icon.json"; exit 1; }
BRAVE="/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
[ -x "$BRAVE" ] || { echo "make-icons: headless Brave not found at $BRAVE"; exit 1; }

WORK="$(mktemp -d -t duoalley-icons)"
trap 'rm -rf "$WORK"' EXIT

# The fill and the layer files, bottom first, from icon.json (the light appearance: the entry with no
# "appearance" key).
python3 -I - "$ICON" "$WORK/icon.html" <<'PY'
import json, pathlib, sys
icon = pathlib.Path(sys.argv[1])
doc = json.loads((icon / "icon.json").read_text())
fill = next(s["value"]["solid"] for s in doc["fill-specializations"] if "appearance" not in s)
r, g, b, a = (float(v) for v in fill.split(":", 1)[1].split(","))
css = f"rgb({round(r * 255)},{round(g * 255)},{round(b * 255)})"
layers = []
for group in reversed(doc["groups"]):
    for layer in reversed(group["layers"]):
        name = next(s["value"] for s in layer["image-name-specializations"] if "appearance" not in s)
        path = icon / "Assets" / name
        if not path.is_file():
            sys.exit(f"make-icons: icon.json names {name}, which is not in Assets/")
        layers.append(path)
imgs = "".join(f'<img src="file://{p}" style="position:absolute;left:0;top:0;width:1024px;height:1024px">'
               for p in layers)
pathlib.Path(sys.argv[2]).write_text(
    '<!doctype html><html><body style="margin:0;background:' + css + '">'
    '<div style="position:relative;width:1024px;height:1024px;background:' + css + '">' + imgs +
    "</div></body></html>")
print("make-icons: fill " + css + ", layers bottom first: " + ", ".join(p.name for p in layers))
PY

"$BRAVE" --headless --disable-gpu --hide-scrollbars --no-first-run --disable-background-networking \
    --disable-component-update --disable-sync --force-device-scale-factor=1 --window-size=1024,1024 \
    --virtual-time-budget=3000 --screenshot="$WORK/full.png" "file://$WORK/icon.html" >/dev/null 2>&1
[ -s "$WORK/full.png" ] || { echo "make-icons: Brave drew nothing"; exit 1; }

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
echo "make-icons: wrote 4 pictures and scripts/icon-source.txt from $ICON"
