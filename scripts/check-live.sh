#!/usr/bin/env bash
# Checks the LIVE site (README.md, "How it was set up").
#
#     scripts/check-live.sh
#
# Network, read only: curl against https://hingealley.com and one App Store lookup. Changes nothing. Run
# it after every push, after any change to _config.yml, and on the day the game goes on sale. Every
# line it prints is PASS or FAIL; it exits non-zero on any FAIL. (Run in the first minute after a
# push, GitHub Pages may still be deploying: give it that minute before believing a FAIL.)
#
# What it holds, and why:
#   - the four pages serve 200 at the trailing slash URLs the app and the listing use, and the bare
#     paths redirect to them (the privacy URL is compiled into the app; a 404 there is a 2.1
#     rejection, and the game's Scripts/preflight-release.sh refuses an archive over it);
#   - the served home and privacy pages are byte for byte this repository's (a push that did not
#     deploy, or a deploy of the wrong branch, looks fine from a browser);
#   - the icons are served byte for byte as this repository has them: a 200 says a file is there, not
#     which picture it is, and the icon changes when the owner picks one (scripts/make-icons.sh);
#   - an unknown path serves the styled 404 with a 404 status;
#   - app-ads.txt is 200, text/plain, at the apex with no redirect, and carries OWNERDOMAIN and the
#     Google seller line;
#   - plain HTTP and www both land on the HTTPS apex;
#   - README.md, scripts/ and _config.yml are NOT served (_config.yml's exclude list keeps them off);
#   - THE "COMING" LINE AGREES WITH THE APP STORE, in both directions. A sibling site said "Coming
#     soon" for three days after its game went on sale. This asks Apple's public lookup whether the
#     game is on sale and fails while the home page disagrees.
set -uo pipefail
SITE="$(cd "$(dirname "$0")/.." && pwd)"
DOMAIN="hingealley.com"
HOST="https://$DOMAIN"
APPLE_ID="6826694965"          # App Store Connect's Apple ID for this game
NOT_FOUND="Gutter ball"        # the 404 page's heading
SELLER='google.com, pub-5706069574815967, DIRECT, f08c47fec0942fa0'
fails=0
pass() { printf 'PASS %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1"; fails=$((fails + 1)); }

status() { curl -sS -o /dev/null -w '%{http_code}' --max-time 20 "$1" 2>/dev/null; }
header() { curl -sSI --max-time 20 "$1" 2>/dev/null | tr -d '\r' | awk -v h="$(tr A-Z a-z <<< "$2")" \
    'BEGIN{FS=": "} tolower($1)==h {print $2}' | tail -1; }
lands() { curl -sS -o /dev/null -L --max-redirs 5 -w '%{http_code} %{url_effective}' --max-time 20 "$1" 2>/dev/null; }
same() { curl -sS --fail --max-time 20 "$HOST$1" 2>/dev/null | cmp -s - "$SITE$2"; }

for path in / /support/ /privacy/ /terms/ /app-ads.txt /robots.txt /sitemap.xml /style.css; do
    code=$(status "$HOST$path")
    [ "$code" = 200 ] && pass "$path is 200 over HTTPS" || fail "$path is $code over HTTPS, expected 200"
done

same / /index.html && pass "the served home page is this repository's index.html, byte for byte" \
    || fail "the served home page differs from index.html (not deployed yet, or the wrong branch)"
same /privacy/ /privacy/index.html && pass "the served privacy page is this repository's, byte for byte" \
    || fail "the served privacy page differs from privacy/index.html (not deployed yet, or the wrong branch)"

for path in /assets/icon-32.png /assets/icon-96.png /assets/icon-180.png /assets/icon-512.png; do
    same "$path" "$path" && pass "$path is this repository's, byte for byte" \
        || fail "$path is missing or differs from the repository's (not deployed, or a stale icon)"
done

for path in /support /privacy /terms; do
    code=$(status "$HOST$path"); loc=$(header "$HOST$path" location)
    if [ "$code" = 301 ] && { [ "$loc" = "$HOST$path/" ] || [ "$loc" = "$path/" ]; }; then pass "$path redirects to $path/"
    else fail "$path is $code to '${loc}', expected 301 to $HOST$path/"; fi
done

type=$(header "$HOST/" content-type)
case "$type" in text/html*) pass "the home page is $type" ;; *) fail "the home page is '$type', expected text/html" ;; esac
type=$(header "$HOST/app-ads.txt" content-type)
case "$type" in text/plain*) pass "app-ads.txt is $type" ;; *) fail "app-ads.txt is '$type', expected text/plain" ;; esac
ads=$(curl -sS --max-time 20 "$HOST/app-ads.txt" 2>/dev/null)
grep -qx "$SELLER" <<< "$ads" && pass "app-ads.txt carries the Google seller line" \
    || fail "app-ads.txt does not carry the Google seller line"
grep -qx "OWNERDOMAIN=$DOMAIN" <<< "$ads" && pass "app-ads.txt declares OWNERDOMAIN=$DOMAIN" \
    || fail "app-ads.txt does not declare OWNERDOMAIN=$DOMAIN"

loc=$(header "http://$DOMAIN/" location)
[ "$loc" = "$HOST/" ] && pass "http:// redirects to the HTTPS apex" || fail "http:// goes to '$loc', expected $HOST/"
loc=$(header "https://www.$DOMAIN/" location)
[ "$loc" = "$HOST/" ] && pass "https://www redirects to the apex" || fail "https://www goes to '$loc', expected $HOST/"
end=$(lands "http://www.$DOMAIN/")
[ "$end" = "200 $HOST/" ] && pass "http://www lands on the HTTPS apex" || fail "http://www lands on '$end', expected 200 $HOST/"

code=$(status "$HOST/no-such-page-$$")
body=$(curl -sS --max-time 20 "$HOST/no-such-page-$$" 2>/dev/null)
if [ "$code" = 404 ] && grep -q "$NOT_FOUND" <<< "$body"; then pass "an unknown path serves the styled 404"
else fail "an unknown path is $code$(grep -q "$NOT_FOUND" <<< "$body" || echo ', not the styled 404')"; fi

for path in /README.md /scripts/lint-site.py /scripts/check-live.sh /scripts/make-icons.sh \
            /scripts/icon-source.txt /scripts/shoot.sh /_config.yml /.gitignore; do
    code=$(status "$HOST$path")
    [ "$code" = 404 ] && pass "$path is not published" || fail "$path is $code: it is PUBLIC (see _config.yml)"
done

# The App Store's own answer. An empty result means not on sale in the US storefront (yet).
count=$(curl -sS --max-time 20 "https://itunes.apple.com/lookup?id=$APPLE_ID" 2>/dev/null \
    | python3 -c 'import json,sys; print(json.load(sys.stdin).get("resultCount", 0))' 2>/dev/null)
says_coming=$(grep -c "Coming to the App Store" "$SITE/index.html")
links_store=$(grep -c "apps.apple.com/app/id$APPLE_ID" "$SITE/index.html")
if [ -z "$count" ]; then
    fail "could not ask the App Store whether the game is on sale"
elif [ "$count" -gt 0 ] && [ "$says_coming" -gt 0 ]; then
    fail "the game is ON SALE and index.html still says 'Coming to the App Store'. README.md, 'Launch day'."
elif [ "$count" -gt 0 ] && [ "$links_store" -eq 0 ]; then
    fail "the game is on sale and index.html has no link to it. README.md, 'Launch day'."
elif [ "$count" -eq 0 ] && [ "$links_store" -gt 0 ]; then
    fail "index.html links to the App Store page of a game that is not on sale"
else
    pass "the home page agrees with the App Store (on sale: $([ "$count" -gt 0 ] && echo yes || echo no))"
fi

echo
[ "$fails" -eq 0 ] && echo "check-live: clean" || echo "check-live: $fails failure(s)"
[ "$fails" -eq 0 ]
