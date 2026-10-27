# hingealley.com

The website of **Hinge Alley**, the boardwalk alley roller as an arcade game for a phone that folds
(bundle `com.duoalley.game`, App Store Connect Apple ID `6826694965`; the game repository is
`therealcreynold/hinge-alley`, checked out beside this one as `../hingealley`, or `../duoalley` before
the folder's rename). It carries the three URLs App Store Connect and the app need, the file advertising
networks crawl, and a home page that says truthfully what the game is.

Hand-written pages, one stylesheet, four icon files. No build step, no framework, no JavaScript, no web
fonts and nothing fetched from another host: every file here is the file that gets served.

| Path | Why it exists |
|---|---|
| `index.html` | The home page and the App Store Connect **Marketing URL** (`https://hingealley.com`, the apex): what the game is, the five modes, the poses, free with ads, "Coming to the App Store." |
| `support/index.html` | The App Store Connect **Support URL** (`https://hingealley.com/support/`): contact, then answers written from the game's code (rolling, the modes, Daily Alley, Pass & Play, the poses, pausing, the +3 balls video, Remove Ads and Restore Purchases, Game Center, sound, ads and choices, phones, data) |
| `privacy/index.html` | The App Store Connect **Privacy Policy URL** (`https://hingealley.com/privacy/`), also compiled into the app (`MoneyLinks.privacyPolicy`). A draft from the build until the game has `docs/PRIVACY-POLICY.md` (below) |
| `terms/index.html` | Terms of use beside Apple's standard licence. In no App Store Connect field; the app does not link it |
| `404.html` | Served by GitHub Pages for any other path ("Gutter ball"), at whatever path was asked for |
| `app-ads.txt` | `OWNERDOMAIN=hingealley.com` and the AdMob publisher account's seller line |
| `sitemap.xml`, `robots.txt` | The four pages; everything crawlable, app-ads.txt above all |
| `style.css` | Every page's styles, light and dark |
| `assets/icon-{32,96,180,512}.png` | The app icon: favicon, header mark, home screen icon and hero, share image. Drawn by `scripts/make-icons.sh` |
| `CNAME` | The custom domain, for GitHub Pages |
| `_config.yml` | The list of things this repository is **not** allowed to publish |
| `scripts/` | The lint, the icon drawer, the page photographer and the live checks. Not published |

## The URLs the listing uses

These are the values in the game's `docs/APP-STORE-LISTING.md` ("The other fields"), and
`scripts/lint-site.py` holds the listing and the app to them whenever the game repository sits beside
this one:

| App Store Connect field | URL |
|---|---|
| Marketing URL | `https://hingealley.com` |
| Support URL | `https://hingealley.com/support/` |
| Privacy Policy URL | `https://hingealley.com/privacy/` (the app's `MoneyLinks.privacyPolicy`, slash included) |
| app-ads.txt (crawled, not typed) | `https://hingealley.com/app-ads.txt` |

The trailing slashes matter: the bare paths answer 301, and the game's `Scripts/preflight-release.sh`
refuses a URL that redirects.

## What the pages say, and why only that

**Every sentence is a claim about the build**, written from the game repository's code and
`docs/DECISIONS.md`, never from the brief: a sibling game once sold a gesture it never had because its
copy was written from the plan. The words a player sees in the game are quoted exactly as the code
spells them, so a player can find the row a page names. When the game changes, the page changes in the
same pass, and its date moves only when it was re-read against the code.

Three things are deliberately **not** said until the owner decides them:

- **Family Sharing** for Remove Ads (the game's O8, irreversible in App Store Connect). The support
  and terms pages say Remove Ads belongs to the Apple Account and comes back with Restore Purchases,
  and nothing about families.
- **The leaderboards and achievements by name and number** (O10; nothing is created in App Store
  Connect yet). The pages say what is and is not sent to Game Center, which is in the code.
- **The price.** The App Store shows it in the visitor's own currency; the lint fails on a currency
  sign before a number.

No App Store link appears until the game is on sale; "Coming to the App Store." is the only word about
availability, and the home page names no date.

## The privacy policy

The game repository is meant to hold the policy as `docs/PRIVACY-POLICY.md`, beside the privacy
manifest and the label it must agree with, and this page is meant to be that file's words, exactly.
**That file does not exist yet** (the game's wave 6 Assets row owns it), so `privacy/index.html` is a
draft written from the build: `PrivacyInfo.xcprivacy` (the binary collects nothing and declares no
tracking domains), `Info.plist`'s tracking string, the `Kit/Ads` code (the pacing in `AdPolicy`, the
tracking card on the first results, the consent gate, the Personalised ads switch, Privacy options,
Report an ad, the Remove Ads sentence), `Kit/Score` (nothing from Pass & Play or a +3 frame posted), the
share card, and the Google Mobile Ads and UMP SDKs' own disclosures.

When `docs/PRIVACY-POLICY.md` lands, either it is written from this page or this page is rewritten to
it; from then on `scripts/lint-site.py` compares the two **word for word** (headings, list markers,
bold and backticks stripped, as the game's `Scripts/preflight-release.sh` compares the served page) and
fails on any difference. **Neither normaliser strips Markdown link syntax**, so the `.md` writes link
text as plain words ("Apple's privacy policy", a bare URL as itself), exactly as the page shows it; the
lint fails on a `[text](url)` or `<https://...>` in the policy. To change the policy after that: the
game's file first, then this page, then push, then archive.

Two things the page now says that the policy must keep: the only thing that reaches us is an email a
player chooses to send (Email support, Report an ad, or the address on this site), kept only until it is
dealt with; and the American states' opt-out is described as Google's Privacy options row **where
Google's consent software shows it**, because the game draws that row only when UMP says it is required
(`Advertising.swift`, `rememberPrivacyOptions` and `adoptPrivacyEvidence`), which for the US states
needs the US states message published in AdMob (part of the game's O7).

For release gating run the lint beside the game repository with `--require-game`, which turns every
SKIP (a missing policy, icon or listing) into a FAIL:

    python3 scripts/lint-site.py --require-game

## The icon, and the one command that redraws it

The owner has not picked the icon yet (the game's O9: five options drawn by
`swift run alley-art icon-options`, option 1 committed as a placeholder). Every picture of the icon on
this site is drawn from **whatever `app/DuoAlley/AppIcon.icon` the game has committed**, by one command:

    scripts/make-icons.sh            # or: scripts/make-icons.sh /path/to/the/game/repository

The game's `node Scripts/compose-creative.mjs` runs it for you after it redraws the store's copies, so in
practice the one command for every copy of the icon, store and site, is that one.

It draws the icon with the game's own renderer, `swift run -c release alley-art marketing-icon` (the one
that draws the store's marketing icon, so the site and the store cannot drift apart), scales it with
sips, drops the alpha channel, and writes `assets/icon-{32,96,180,512}.png` plus `scripts/icon-source.txt`, the SHA-256
of every file it read. It refuses while `AppIcon.icon` has uncommitted changes in the game repository
(edited, staged or untracked), and the lint hashes the **HEAD** blobs through git, never the working
tree, so an icon nobody has committed can neither be drawn nor pass. Icon Composer's glass and drop shadows are not drawn: what comes out is the flat
artwork. `scripts/lint-site.py` fails while the game's committed `AppIcon.icon` differs from the files
recorded in `scripts/icon-source.txt`, so after the owner picks and the game commits the new icon:

    scripts/make-icons.sh && python3 scripts/lint-site.py && scripts/shoot.sh /tmp/duoalley/site-shots

then look at the pictures and commit them with `scripts/icon-source.txt`.

## Words that must never appear on this site

The game's house rules (its CLAUDE.md, "Style and legal", and decision 34), and they hold here because
a web page is what a search engine reads and what a lawyer is shown, and this repository is public:

- **No em or en dash**, anywhere, as a character or an entity.
- **No protected name**: the trademark word the game's brief names (as a word or the start of one), its
  licensor and licensee, the competitors and publishers the brief lists, the arcade basketball machine,
  league abbreviations, the catch phrase.
- **None of the owner's other games**, by name or by link, the sibling Duo games included.
- **The device's name only as a platform statement** ("Designed for iPhone Duo"), never in prose and
  never as part of the game's name. The prose says "a phone that folds".
- **No price.**
- **The game's name is Hinge Alley** (the owner's rename, 27 October 2026, so that no player-facing
  name leans on Apple's product name). The former two-word name appears in no file but `app-ads.txt`,
  whose comments are kept exactly. What stays is permanent or invisible: this repository's name, the
  bundle id and the game's `DuoAlley` folders. The domain moved to `hingealley.com` the same day (the
  owner's call); `duoalley.com` redirects to it.
  Every page's `<title>` names Hinge Alley and its `og:site_name` is exactly that.
- **No dating language.** Our hinge is the phone's fold, and a dating app of that name exists, so no
  page says "a perfect match", matchmaking, dating, swipe, soulmate or the like. A Pass & Play match
  is a game, and the word stays in that sense.

`scripts/lint-site.py` enforces these over every text file in the repository, this README and its own
source included, with its patterns spelled in pieces so it does not fail its own scan; `--self-test`
proves each pattern still catches what it should and lets near misses through. It also fails on a
script, an iframe, a form, an inline handler or style, a web font, any `url(` in the stylesheet, a
picture that is not one of the icons, an image whose declared size is not the file's, an icon with
alpha, an external link off its allowlist (Apple's licence, privacy and refund pages, Google's two
privacy pages), a mailto that is not the contact address, a link that does not resolve or drops its
trailing slash, a missing title, viewport, stylesheet, icon or canonical URL, a date on the home page,
Liquid syntax or front matter, `app-ads.txt`, `robots.txt`, `sitemap.xml`, `CNAME` or `_config.yml`
drifting from this README, and **any published file that is not in its list**. Run it before every
commit:

    python3 scripts/lint-site.py

## What this repository publishes

**Only what `_config.yml` allows.** GitHub Pages deploys every file in a repository by default, so
without it this README and `scripts/` would be public pages. `.nojekyll` cannot help: with Jekyll off
there is no ignore list at all. So Jekyll is on, and `exclude:` names `README.md` and `scripts`. Jekyll
copies every page byte for byte because none has front matter or Liquid syntax, and the lint fails if
one ever does. Anything added here is public the moment it is pushed unless it is named in
`_config.yml`; add it there first, and re-run `scripts/check-live.sh` after any change to that file.

## Looking at it

A lint asserts what a file holds; a defect is a fact about what a page draws. Every page is
photographed before a commit:

    scripts/shoot.sh /tmp/duoalley/site-shots

That renders the five pages with headless Brave from **local files only** (the root relative URLs are
rewritten in a temporary copy, never here), at 1280 px and at a 390 px phone width drawn at 2x, in light
and dark, and reports any page wider than its window. A headless window is never narrower than 500 px,
so the phone width is an iframe of exactly 390 px. Then open every slice and read it.

## Publishing (the owner's step)

Nothing here is pushed by an agent. To publish what is committed:

    git -C ../duoalley-website push origin main
    scripts/check-live.sh            # give GitHub Pages a minute after the push

Until that push the live site is still the holding page, and `scripts/check-live.sh` fails on the
pages, `app-ads.txt` and the icons it cannot find (17 FAIL and 17 PASS on 26 October 2026, against the
holding page). After it, every line should be PASS.

Once the AdMob app exists (the game's O7) and is linked to the live store listing, open AdMob's own
"Set up app-ads.txt" dialog for it and confirm the Google line in `app-ads.txt` matches byte for byte;
if it ever differs, the dialog wins. Never type or guess a seller line, and add another network's lines
only when that network is enabled in the shipping build, pasted from its own dashboard. Crawling starts
from the store listing's Marketing URL, so allow about 24 hours after both are live.

## The DNS

hingealley.com is the site's domain since 27 October 2026 (the owner's call; before that it was
duoalley.com, registered at Namecheap, which now redirects to hingealley.com from a separate
repository). These nine records point it at GitHub Pages, the same nine the owner's other game sites
use, and the owner had set them on hingealley.com before the switch. An apex domain needs A and AAAA
records rather than a CNAME:

| Type | Host | Value |
|---|---|---|
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| AAAA | @ | 2606:50c0:8000::153 |
| AAAA | @ | 2606:50c0:8001::153 |
| AAAA | @ | 2606:50c0:8002::153 |
| AAAA | @ | 2606:50c0:8003::153 |
| CNAME | www | therealcreynold.github.io |

All four of each, not one: they are GitHub's edge addresses, and dropping some costs availability
rather than breaking the site outright. Namecheap's parking records on a new domain (a `CNAME www` to
`parkingpage.namecheap.com` and a `URL Redirect @`) go; the email forwarding MX and SPF records stay.
Read what is there before changing anything:

    dig +short @1.1.1.1 hingealley.com A
    dig +short @1.1.1.1 hingealley.com AAAA
    dig +short @1.1.1.1 www.hingealley.com CNAME

The contact address is **info@crindustries.xyz**, the one the owner's other games and their sites use.
Nothing here needs email at either domain, so no forwarding address was configured.

## How it was set up

**DONE 25 October 2026 for duoalley.com, and live over HTTPS; MOVED to hingealley.com on 27 October
2026.** The move is this repository's `CNAME` (now `hingealley.com`) plus steps 3, 5, 6 and 7 below run
again for the new domain after the push; until GitHub's certificate covers hingealley.com,
`scripts/check-live.sh` fails. What follows is the first setup, for duoalley.com. The repository
`therealcreynold/duoalley-website` was created public and pushed; Pages was enabled from `main` at the
root with the custom domain `duoalley.com`; the nine DNS records were set at Namecheap the same day;
GitHub's certificate reached `approved` (covering `duoalley.com` and `www.duoalley.com`) within
minutes and `https_enforced` was set; `scripts/check-live.sh` then printed 16 PASS and "clean" against the holding page. (Run in the first
minute after the certificate was approved, it failed twice, on `www` and on one connection, while the
certificate reached GitHub's edge; a minute later it was clean.) The steps stay because they are how
the site gets rebuilt. Read what is there before redoing anything. In order:

1. **The repository** `therealcreynold/duoalley-website`, **public** (GitHub Pages on a free account
   serves only public repositories), created empty and pushed from `main`.
2. **Pages**: deploy from the branch `main`, folder `/ (root)`, through the API:

       gh api -X POST repos/therealcreynold/duoalley-website/pages \
         -f 'source[branch]=main' -f 'source[path]=/'

3. **The custom domain** `hingealley.com` (the committed `CNAME` agrees):

       gh api -X PUT repos/therealcreynold/duoalley-website/pages -f cname=hingealley.com

4. **The DNS** above, at Namecheap.
5. **Wait for GitHub's certificate** to reach `approved`, covering the apex and `www`:

       gh api repos/therealcreynold/duoalley-website/pages --jq .https_certificate

6. **Enforce HTTPS**:

       gh api -X PUT repos/therealcreynold/duoalley-website/pages -F https_enforced=true

7. Run `scripts/check-live.sh` until it is clean.

## Checking it actually works

    scripts/check-live.sh

Network, read only. It holds that the four pages, `app-ads.txt`, `robots.txt`, `sitemap.xml` and the
stylesheet are 200 over HTTPS at their trailing slash URLs and the bare paths 301 to them; that the
home and privacy pages and every icon are byte for byte this repository's; that `app-ads.txt` is
`text/plain` with `OWNERDOMAIN` and the seller line; that `http://`, `https://www` and `http://www` all
land on `https://hingealley.com/`; that an unknown path is a 404 with the styled page; that `README.md`,
`scripts/`, `_config.yml` and `.gitignore` are **not** served; and that the page agrees with the App
Store: it asks Apple's public lookup for Apple ID `6826694965` and fails if the game is on sale while
the page still says "Coming to the App Store." or has no link to it, and if the page links to a store
page that is not on sale.

## Launch day

On the day the game goes on sale, "Coming to the App Store." becomes a link to
`https://apps.apple.com/app/id6826694965` (no country code, so each visitor lands in their own
storefront), `apps.apple.com` goes onto `LINK_HOSTS` in `scripts/lint-site.py` and the "Coming" rule
there changes with it; `scripts/check-live.sh` fails until both are done. The game's own screenshots,
once its wave 6 Assets row has captured them from the build, can join the icon then, drawn by the game
and never retouched.
