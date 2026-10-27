#!/usr/bin/env python3
"""The site's gate: run it before every commit that touches a word or a file.

    python3 scripts/lint-site.py              everything, offline
    python3 scripts/lint-site.py --self-test  proves every pattern catches what it should

Ported from the owner's other game sites. It needs nothing but Python 3 and macOS's sips, and never
touches the network. What it fails on, and why each one is here:

  WORDS (every text file in the repository, this one included, README and comments included, because
  the repository itself is public on GitHub):
  - an em or en dash, as a character or as an HTML entity. The game's house rule: no em or en dash in
    any user-facing string, and a website is nothing but user-facing strings.
  - a protected name, the same list the game repository's Scripts/lint-store-copy.py holds: the
    trademark word GAME.md line 5 names, as a word or the start of one (so every spelling and every
    product built on it), its licensor and licensee, the competitors and publishers GAME.md 3 names,
    the arcade basketball machine, the league abbreviations, the catch phrase, and the developer's
    other apps, the sibling Duo games included. Spelled in pieces, so this file does not trip its own
    scan.
  - the device's name anywhere but a "Designed for iPhone Duo" statement, in the published files.
  - the game's former name (two words, the first the one Apple's device carries; the owner renamed
    the game Hinge Alley on 27 October 2026 so that no player-facing name leans on Apple's product
    name), in any text file but app-ads.txt, whose comments are a contract kept exactly. The domain,
    the bundle id, the repository names and the game's DuoAlley folders are one word or hyphenated,
    and stay.
  - dating language in the published files: "hinge" here is the phone's fold, and a dating app of
    that name exists, so no page says "a perfect match", matchmaking, dating, swipe or the like (a
    Pass & Play match is a game, and stays).
  - a price (a currency sign before a number) in the published files: the App Store shows the price,
    in the visitor's own currency, and a page that names one is wrong somewhere the day it is read.

  THE PUBLISHED FILES (everything _config.yml does not exclude):
  - exactly the files in PUBLISHED, no more and no fewer. A file added by accident is public the
    moment it is pushed.
  - a Liquid tag opener or YAML front matter (Jekyll copies a page byte for byte only while it has
    neither; see _config.yml).
  - a <script>, an inline event handler, an iframe, a form, a web font, an @import, inline styles, any
    url( in the stylesheet, or anything loaded from another host. The site runs no code and fetches
    nothing from anybody else.
  - a picture that is not one of the icons or the store screenshots in assets/, an <img> without alt or
    whose width and height are not the file's, a screenshot with an alpha channel, a favicon or home screen icon missing from a page or not the size it claims,
    and an icon with an alpha channel.
  - a link to a host not on LINK_HOSTS (an App Store link is refused until the game is on sale: add
    apps.apple.com then, README.md "Launch day"), a plain http link, a mailto that is not the contact
    address, a relative URL, a root relative link or fragment that does not resolve, and a link to a
    page without its trailing slash (that is a redirect, and the app and the listing hold the slash).
  - a page without the doctype, a viewport, a title or the stylesheet; a title that does not name the
    game (NAME), an og:site_name that is not NAME; a page other than the 404 without its canonical URL; a home page without "Coming to the App Store." exactly once, or naming
    a date.

  THE FILES THAT ARE CONTRACTS: CNAME; app-ads.txt (OWNERDOMAIN and the Google seller line, exactly,
  and nothing else); robots.txt (no Disallow, the Sitemap line); sitemap.xml (exactly the four pages);
  _config.yml (its exclude list is NOT_PUBLISHED below, exactly); and no .nojekyll.

  THE GAME REPOSITORY, when it sits beside this one (../hingealley, or ../duoalley before the rename; each check is SKIPPED, and says so,
  when the file it needs is not there; with --require-game every SKIP is a FAIL, which is how a release
  is gated):
  - privacy/index.html against docs/PRIVACY-POLICY.md, WORD FOR WORD: the policy is that file's text
    and only that file's text, compared the way the game's Scripts/preflight-release.sh compares the
    served page. Neither normaliser strips Markdown link syntax, so the policy writes link text as plain
    words, and a Markdown link in it is a FAIL here.
  - the icons against the game's committed app/DuoAlley/AppIcon.icon (the blobs at HEAD, read through
    git, never the working tree): scripts/icon-source.txt records
    the files scripts/make-icons.sh drew from, and a difference means the site shows an icon the game
    no longer has. Run scripts/make-icons.sh.
  - the screenshots against the game's committed framed store screenshots, the same way:
    scripts/shot-source.txt records what scripts/make-shots.sh copied. Run scripts/make-shots.sh.
  - the privacy URL compiled into the app (MoneyLinks.privacyPolicy) and the Support and Marketing
    URLs in docs/APP-STORE-LISTING.md name pages this site has.
"""

from __future__ import annotations

import hashlib
import html
import html.parser
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
# The game's checkout beside this one: ../hingealley after the folder's rename, ../duoalley before it.
GAME = next((ROOT.parent / d for d in ("hingealley", "duoalley") if (ROOT.parent / d).is_dir()),
            ROOT.parent / "hingealley")
DOMAIN = "hingealley.com"               # the domain since 27 October 2026; duoalley.com redirects here
NAME = "Hinge Alley"                    # the game's player-facing name (27 October 2026)
CONTACT = "info@crindustries.xyz"
PAGES = ["index.html", "support/index.html", "privacy/index.html", "terms/index.html"]
ICONS = {"assets/icon-32.png": 32, "assets/icon-96.png": 96, "assets/icon-180.png": 180,
         "assets/icon-512.png": 512}
# The store's own framed screenshots, copied by scripts/make-shots.sh (JPEG, no alpha).
SHOTS = {"assets/shots/hundred.jpg", "assets/shots/closed.jpg", "assets/shots/phone.jpg"}
PUBLISHED = set(PAGES) | set(ICONS) | SHOTS | {"404.html", "style.css", "CNAME", "robots.txt", "sitemap.xml",
                                       "app-ads.txt"}
NOT_PUBLISHED = {"scripts", "README.md"}            # must agree with _config.yml's exclude list
TEXT_SUFFIXES = {".html", ".css", ".txt", ".xml", ".yml", ".md", ".py", ".sh", ""}
SELLER_LINE = "google.com, pub-5706069574815967, DIRECT, f08c47fec0942fa0"

# Hosts a page may link out to. Each is somewhere a player is sent on purpose: Apple's licence,
# privacy policy and refund page, and Google's two privacy pages the policy cites.
LINK_HOSTS = {"www.apple.com", "reportaproblem.apple.com", "policies.google.com"}

# Spelled in pieces so that this file does not fail its own scan (it is scanned like every other
# file). Every piece holding a backslash is a raw string: a plain "\b" is a backspace, and a pattern
# built with one silently matches nothing.
PROTECTED = [
    (re.compile(r"\bs" + r"kee", re.I), "the trademark word GAME.md line 5 names, or a word built on it"),
    (re.compile(r"\bbay[\s-]?" + r"tek\b", re.I), "the trademark's licensee (GAME.md line 5)"),
    (re.compile(r"\bdimensional\s+" + r"branding\b", re.I), "the trademark's licensor (GAME.md line 5)"),
    (re.compile(r"\bocean\s+" + r"media\b", re.I), "a competitor's publisher (GAME.md 3)"),
    (re.compile(r"\bscope" + r"ly\b", re.I), "a competitor's publisher (GAME.md 3)"),
    (re.compile(r"\bbig[\s-]?" + r"cave\b", re.I), "a competitor's studio (GAME.md 3)"),
    (re.compile(r"\bskill" + r"z\b", re.I), "a competitor's platform (GAME.md 3)"),
    (re.compile(r"\bfree" + r"verse\b", re.I), "a competitor's publisher (GAME.md 3)"),
    (re.compile(r"\bball[\s-]?" + r"master\b", re.I), "a competitor's app (GAME.md 3)"),
    (re.compile(r"pop[\s-]?a[\s-]?" + "shot", re.I), "a registered trademark (an arcade basketball machine)"),
    (re.compile(r"\b(" + "N" + "BA|W" + "N" + "BA|N" + "CAA|FI" + "FA|UE" + "FA|M" + "LS" + r")\b"),
     "a league or governing body"),
    (re.compile(r"he['\u2019]?s on " + "fire", re.I), "a catch phrase the house forbids"),
    (re.compile(r"\b(" + "muta" + "bloom|crater" + "gut|turf" + "storm|wen" + "dra|where" + r"isit)\b", re.I),
     "another of the developer's apps (the site names none of them)"),
    (re.compile(r"\bhalf[\s-]?" + r"court\b", re.I), "a sibling app's name (the sibling Duo games)"),
    (re.compile(r"\bduo[\s-]?" + "shoot" + r"out\b", re.I), "a sibling app's name (the sibling Duo games)"),
]
DASH = re.compile("[\u2013\u2014]|&[mn]dash;|&#(8211|8212|x201[34]);", re.I)
DEVICE = re.compile(r"iphone\s+duo", re.I)
DEVICE_ALLOWED = re.compile(r"Designed for iPhone Duo")
# The former name, in pieces. Two words only: "duoalley.com" (the former domain, now a redirect),
# "app/DuoAlley" and "duo-alley" are identifiers and do not match.
OLD_NAME = re.compile(r"\bduo[ \t]+" + r"alley\b", re.I)
OLD_NAME_ALLOWED = {"app-ads.txt"}
# A game "match" (a Pass & Play match) is a game word and is allowed; the dating senses are not.
DATING = re.compile(r"\b((perfect|a|your|it'?s[ \t]+a)[ \t]+match|match(ed|maker|making)|dat(e|es|ing)[ \t]+(night|app)s?"
                    r"|dating|swip(e|es|ed|ing)|soul[ -]?mates?|flirt\w*|romanc\w*|crush(es)?)\b", re.I)
PRICE = re.compile("[$\u20ac\u00a3\u00a5]\\s?\\d|\\b(USD|EUR|GBP)\\s?\\d|\\d\\s?(USD|EUR|GBP)\\b")
# Months capitalized (so "may" and "march" stay words), seasons either way; "fall" is left out.
DATE = re.compile(r"\b(19|20)\d\d\b|\b(January|February|March|April|May|June|July|August|September|"
                  r"October|November|December)\b|\b([Ss]pring|[Ss]ummer|[Aa]utumn|[Ww]inter)\b")


def published_files() -> list[pathlib.Path]:
    out = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        top = path.relative_to(ROOT).parts[0]
        if top.startswith(".") or top.startswith("_") or top in NOT_PUBLISHED:
            continue
        out.append(path)
    return out


def text_files() -> list[pathlib.Path]:
    out = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.relative_to(ROOT).parts[:1]:
            continue
        if path.name == ".DS_Store" or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        out.append(path)
    return out


def rel(path: pathlib.Path) -> str:
    return str(path.relative_to(ROOT))


def check_words(problems: list[str]) -> None:
    published = set(published_files())
    for path in text_files():
        for number, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            if DASH.search(line):
                problems.append(f"{rel(path)}:{number}: an em or en dash")
            for pattern, why in PROTECTED:
                if pattern.search(line):
                    problems.append(f"{rel(path)}:{number}: {why}")
            if rel(path) not in OLD_NAME_ALLOWED and OLD_NAME.search(line):
                problems.append(f"{rel(path)}:{number}: the game's former name (it is {NAME} now)")
            if path in published and DATING.search(line):
                problems.append(f"{rel(path)}:{number}: dating language ({DATING.search(line).group(0)!r}); "
                                "our hinge is the phone's fold")
            if path in published and DEVICE.search(DEVICE_ALLOWED.sub("", line)):
                problems.append(f"{rel(path)}:{number}: the device's name outside 'Designed for iPhone Duo'")
            if path in published and PRICE.search(line):
                problems.append(f"{rel(path)}:{number}: a price ({PRICE.search(line).group(0)!r}); the App Store shows it")
    for path in ROOT.rglob("*"):                      # a file name is as public as a sentence
        if ".git" in path.relative_to(ROOT).parts[:1]:
            continue
        for pattern, why in PROTECTED:
            if pattern.search(path.name):
                problems.append(f"{rel(path)}: {why}, in the file name")


class Page(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.main_text: list[str] = []
        self.in_main = 0

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, {k: (v or "") for k, v in attrs}))
        if tag == "main":
            self.in_main += 1

    def handle_endtag(self, tag):
        if tag == "main":
            self.in_main -= 1

    def handle_data(self, data):
        if self.in_main:
            self.main_text.append(data)


_png: dict[pathlib.Path, tuple[int, int, bool] | None] = {}


def png_info(path: pathlib.Path) -> tuple[int, int, bool] | None:
    """(width, height, has alpha) by sips, or None."""
    if path not in _png:
        try:
            out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", "-g", "hasAlpha", str(path)],
                                 capture_output=True, text=True, check=True).stdout
            w = re.search(r"pixelWidth: (\d+)", out)
            h = re.search(r"pixelHeight: (\d+)", out)
            a = re.search(r"hasAlpha: (\w+)", out)
            _png[path] = (int(w.group(1)), int(h.group(1)), a is not None and a.group(1) == "yes") if w and h else None
        except (OSError, subprocess.CalledProcessError):
            _png[path] = None
    return _png[path]


def resolve(url: str) -> pathlib.Path | None:
    """A root relative URL to the file GitHub Pages would serve for it, or None."""
    path = url.split("#", 1)[0].split("?", 1)[0]
    if not path.startswith("/"):
        return None
    target = ROOT / path.lstrip("/")
    if path.endswith("/"):
        target = target / "index.html"
    return target if target.is_file() else None


def check_published(problems: list[str]) -> None:
    have = {rel(p) for p in published_files()}
    for extra in sorted(have - PUBLISHED):
        problems.append(f"{extra} would be published: name it in _config.yml, or add it to PUBLISHED and README.md")
    for missing in sorted(PUBLISHED - have):
        problems.append(f"{missing} is missing")

    css = (ROOT / "style.css").read_text(encoding="utf-8") if (ROOT / "style.css").exists() else ""
    for needle, why in (("url(", "a url( (the stylesheet fetches nothing)"),
                        ("@import", "an @import"), ("@font-face", "a web font")):
        if needle in css:
            problems.append(f"style.css: {why}")

    for name, size in ICONS.items():
        info = png_info(ROOT / name) if (ROOT / name).is_file() else None
        if info is None:
            continue
        if info[:2] != (size, size):
            problems.append(f"{name} is {info[0]} x {info[1]}, expected {size} x {size}")
        if info[2]:
            problems.append(f"{name} has an alpha channel (scripts/make-icons.sh writes opaque files)")
    for name in sorted(SHOTS):
        info = png_info(ROOT / name) if (ROOT / name).is_file() else None
        if info and info[2]:
            problems.append(f"{name} has an alpha channel (scripts/make-shots.sh writes JPEG)")


def check_pages(problems: list[str]) -> None:
    for path in published_files():
        if path.suffix != ".html":
            continue
        text = path.read_text(encoding="utf-8")
        name = rel(path)
        if text.startswith("---"):
            problems.append(f"{name}: YAML front matter (Jekyll would render this page)")
        if "{" + "{" in text or "{" + "%" in text:
            problems.append(f"{name}: a Liquid tag opener (Jekyll would rewrite this page)")
        if not text.lower().startswith("<!doctype html>"):
            problems.append(f"{name}: does not begin with <!doctype html>")
        if re.search(r"\son[a-z]+\s*=", text, re.I):
            problems.append(f"{name}: an inline event handler (the site runs no code)")
        if "@font-face" in text or "@import" in text or "<style" in text.lower() or re.search(r"\sstyle\s*=", text):
            problems.append(f"{name}: inline styles or a web font (everything lives in /style.css)")

        page = Page()
        page.feed(text)
        tags = page.tags
        names = [t for t, _ in tags]
        for banned in ("script", "iframe", "object", "embed", "form", "base"):
            if banned in names:
                problems.append(f"{name}: a <{banned}> (the site runs no code and collects nothing)")
        for banned in ("picture", "svg", "video", "audio", "canvas"):
            if banned in names:
                problems.append(f"{name}: a <{banned}> (the only pictures are the icons and screenshots in assets/)")
        metas = {a.get("name") or a.get("property"): a.get("content", "") for t, a in tags if t == "meta"}
        if "viewport" not in metas:
            problems.append(f"{name}: no viewport meta")
        if "title" not in names:
            problems.append(f"{name}: no <title>")
        else:
            title = re.search(r"<title>(.*?)</title>", text, re.S | re.I)
            if not title or NAME not in html.unescape(title.group(1)):
                problems.append(f"{name}: the <title> does not name {NAME}")
        if "og:site_name" in metas and metas["og:site_name"] != NAME:
            problems.append(f"{name}: og:site_name is {metas['og:site_name']!r}, expected {NAME!r}")
        links = [a for t, a in tags if t == "link"]
        if not any(a.get("rel") == "stylesheet" and a.get("href") == "/style.css" for a in links):
            problems.append(f"{name}: does not link /style.css")
        canon = [a.get("href", "") for a in links if a.get("rel") == "canonical"]
        if name == "404.html":
            if canon:
                problems.append(f"{name}: a canonical URL (the 404 is served at every missing path)")
        else:
            expected = f"https://{DOMAIN}/" + (name[: -len("index.html")] if name.endswith("index.html") else name)
            if canon != [expected]:
                problems.append(f"{name}: canonical is {canon}, expected [{expected!r}]")
        if name == "index.html":
            main_text = " ".join("".join(page.main_text).split())
            if main_text.count("Coming to the App Store.") != 1:
                problems.append(f"{name}: the page must say 'Coming to the App Store.' exactly once")
            if DATE.search(main_text):
                problems.append(f"{name}: a date ({DATE.search(main_text).group(0)!r}); the page promises none")

        if "og:image" in metas:
            prefix = f"https://{DOMAIN}/"
            url = metas["og:image"]
            target = resolve("/" + url[len(prefix):]) if url.startswith(prefix) else None
            if target is None:
                problems.append(f"{name}: og:image {url} does not name a file in this repository")
            else:
                info = png_info(target)
                declared = (metas.get("og:image:width"), metas.get("og:image:height"))
                if info and declared != (str(info[0]), str(info[1])):
                    problems.append(f"{name}: og:image says {declared[0]} x {declared[1]}, the file is {info[0]} x {info[1]}")
        # The favicon and the home screen icon, on every page, at the size each claims.
        for kind in ("icon", "apple-touch-icon"):
            found = [a for a in links if a.get("rel") == kind]
            if len(found) != 1:
                problems.append(f"{name}: {len(found)} <link rel={kind}>, expected one")
                continue
            target, sizes = resolve(found[0].get("href", "")), found[0].get("sizes", "")
            info = png_info(target) if target is not None else None
            if target is None:
                problems.append(f"{name}: <link rel={kind}> {found[0].get('href')} does not resolve")
            elif info and sizes != f"{info[0]}x{info[1]}":
                problems.append(f"{name}: <link rel={kind}> says sizes={sizes!r}, the file is {info[0]}x{info[1]}")

        ids = {a.get("id") for _, a in tags}
        for tag, a in tags:
            for attr in ("href", "src"):
                url = a.get(attr)
                if url is None:
                    continue
                if url.startswith(("http://", "https://", "//")):
                    host = re.sub(r"^(https?:)?//", "", url).split("/", 1)[0]
                    if tag == "link" and a.get("rel") == "canonical":
                        if host != DOMAIN:
                            problems.append(f"{name}: a canonical URL on another host: {url}")
                    elif tag != "a":
                        problems.append(f"{name}: <{tag} {attr}> loads from another host: {url}")
                    elif url.startswith("http://"):
                        problems.append(f"{name}: a plain http link: {url}")
                    elif host not in LINK_HOSTS:
                        problems.append(f"{name}: a link to {host}, which is not on LINK_HOSTS")
                elif url.startswith("mailto:"):
                    if url != f"mailto:{CONTACT}" and not url.startswith(f"mailto:{CONTACT}?subject="):
                        problems.append(f"{name}: a mailto that is not the contact address: {url}")
                elif url.startswith("#"):
                    if url[1:] and url[1:] not in ids:
                        problems.append(f"{name}: a fragment link to #{url[1:]}, which no element has")
                elif url.startswith("/"):
                    target = resolve(url)
                    if target is None:
                        problems.append(f"{name}: {url} does not resolve to a file here")
                        continue
                    bare = url.split("#", 1)[0]
                    if bare.endswith(".html") or (target.name == "index.html" and not bare.endswith("/")):
                        problems.append(f"{name}: link {url} without the trailing slash (a redirect)")
                    frag = url.split("#", 1)[1] if "#" in url else ""
                    if frag and f'id="{frag}"' not in target.read_text(encoding="utf-8"):
                        problems.append(f"{name}: {url} points at #{frag}, which that page does not have")
                else:
                    problems.append(f"{name}: a relative URL {url!r} (use root relative: the 404 is served at any path)")
            if tag == "img":
                src = a.get("src", "")
                if src.lstrip("/") not in ICONS and src.lstrip("/") not in SHOTS:
                    problems.append(f"{name}: <img {src}> is not one of the icons or screenshots in assets/")
                target = resolve(src)
                info = png_info(target) if target is not None else None
                declared = (a.get("width"), a.get("height"))
                if info and declared != (str(info[0]), str(info[1])):
                    problems.append(f"{name}: <img {src}> says {declared[0]} x {declared[1]}, the file is {info[0]} x {info[1]}")
                if "alt" not in a:
                    problems.append(f"{name}: <img {src}> has no alt attribute")


def check_contracts(problems: list[str]) -> None:
    cname = (ROOT / "CNAME").read_text().strip() if (ROOT / "CNAME").exists() else None
    if cname != DOMAIN:
        problems.append(f"CNAME is {cname!r}, expected {DOMAIN!r}")

    ads = (ROOT / "app-ads.txt").read_text() if (ROOT / "app-ads.txt").exists() else ""
    lines = [l.strip() for l in ads.splitlines() if l.strip() and not l.strip().startswith("#")]
    if f"OWNERDOMAIN={DOMAIN}" not in lines:
        problems.append(f"app-ads.txt: no OWNERDOMAIN={DOMAIN} line")
    if SELLER_LINE not in lines:
        problems.append("app-ads.txt: the Google seller line is missing or altered")
    extra = [l for l in lines if l not in (f"OWNERDOMAIN={DOMAIN}", SELLER_LINE)]
    if extra:
        problems.append(f"app-ads.txt: lines nobody pasted from a network's dashboard: {extra}")

    robots = (ROOT / "robots.txt").read_text() if (ROOT / "robots.txt").exists() else ""
    if re.search(r"^\s*Disallow:\s*\S", robots, re.M):
        problems.append("robots.txt: a Disallow (app-ads.txt must stay crawlable)")
    if f"Sitemap: https://{DOMAIN}/sitemap.xml" not in robots:
        problems.append("robots.txt: no Sitemap line")

    sitemap = (ROOT / "sitemap.xml").read_text() if (ROOT / "sitemap.xml").exists() else ""
    locs = re.findall(r"<loc>([^<]+)</loc>", sitemap)
    wanted = [f"https://{DOMAIN}/" + p[: -len("index.html")] for p in PAGES]
    if sorted(locs) != sorted(wanted):
        problems.append(f"sitemap.xml lists {locs}, expected {wanted}")

    config = (ROOT / "_config.yml").read_text() if (ROOT / "_config.yml").exists() else ""
    excluded = set(re.findall(r"^\s*-\s*(\S+)\s*$", config, re.M))
    if excluded != NOT_PUBLISHED:
        problems.append(f"_config.yml excludes {sorted(excluded)}; this script believes {sorted(NOT_PUBLISHED)}")
    if (ROOT / ".nojekyll").exists():
        problems.append(".nojekyll exists: with Jekyll off, _config.yml's exclude list is ignored")


def words(text: str) -> list[str]:
    return re.findall(r"[^\s]+", text)


def check_policy(problems: list[str], notes: list[str]) -> None:
    source = GAME / "docs" / "PRIVACY-POLICY.md"
    if not source.is_file():
        notes.append(f"SKIP the privacy page against the policy: {source} is not written yet "
                     "(privacy/index.html is a draft from the build; the game's Assets row reconciles)")
        return
    md = source.read_text(encoding="utf-8")
    # Neither this lint nor the game's preflight-release.sh (policy_verdict) strips Markdown link syntax,
    # and the two normalisers must stay identical, so the policy writes link text as plain words.
    for link in re.findall(r"\[[^\]\n]+\]\([^)\n]+\)|<https?://[^>\s]+>", md):
        problems.append(f"docs/PRIVACY-POLICY.md has Markdown link syntax {link!r}: write the link text as "
                        "plain words (and a bare URL as itself), as privacy/index.html shows it")
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)            # the file's own note to the reader
    md = re.sub(r"^#+\s*", "", md, flags=re.M)                # headings
    md = re.sub(r"^\s*-\s+", "", md, flags=re.M)              # list markers
    md = md.replace("**", "").replace("`", "")
    page = Page()
    page.feed((ROOT / "privacy" / "index.html").read_text(encoding="utf-8"))
    ours = html.unescape("".join(page.main_text))
    a, b = words(md), words(ours)
    if a == b:
        notes.append(f"privacy/index.html is docs/PRIVACY-POLICY.md word for word ({len(a)} words)")
        return
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    problems.append(
        "privacy/index.html differs from docs/PRIVACY-POLICY.md at word "
        f"{i + 1}: the policy has {' '.join(a[max(0, i - 6):i + 8])!r}, "
        f"the page has {' '.join(b[max(0, i - 6):i + 8])!r}")


def check_icon_source(problems: list[str], notes: list[str]) -> None:
    rel = "app/DuoAlley/AppIcon.icon"
    record = ROOT / "scripts" / "icon-source.txt"
    if not record.is_file():
        problems.append("scripts/icon-source.txt is missing: run scripts/make-icons.sh")
        return
    if not (GAME / rel / "icon.json").is_file():
        notes.append(f"SKIP the icons against the game's AppIcon.icon: {GAME / rel} is not here")
        return
    recorded = {}
    for line in record.read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            digest, name = line.split(None, 1)
            recorded[name.strip()] = digest
    # The COMMITTED icon: the blobs at HEAD, never the working tree, so an uncommitted icon cannot pass.
    def git(*args: str) -> bytes:
        return subprocess.run(["git", "-C", str(GAME), *args], check=True, capture_output=True).stdout
    try:
        names = [n for n in git("ls-tree", "-r", "--name-only", "HEAD", "--", rel).decode().splitlines()
                 if n == f"{rel}/icon.json" or (n.startswith(f"{rel}/Assets/") and n.endswith(".png")
                                                and "/" not in n[len(f"{rel}/Assets/"):])]
        current = {n[len(rel) + 1:]: hashlib.sha256(git("show", f"HEAD:{n}")).hexdigest() for n in names}
        dirty = git("status", "--porcelain", "--untracked-files=all", "--", rel).decode().strip()
    except (OSError, subprocess.CalledProcessError) as error:
        problems.append(f"cannot read the game's committed AppIcon.icon from git: {error}")
        return
    if dirty:
        notes.append(f"the game's {rel} has uncommitted changes; compared against HEAD, which is what ships")
    if recorded != current:
        changed = sorted(k for k in set(recorded) | set(current) if recorded.get(k) != current.get(k))
        problems.append("the site's icons were drawn from an AppIcon.icon the game has not committed "
                        f"({', '.join(changed)}): run scripts/make-icons.sh, look, and commit")
    else:
        notes.append("the icons were drawn from the game's committed AppIcon.icon (HEAD)")


def check_shot_source(problems: list[str], notes: list[str]) -> None:
    record = ROOT / "scripts" / "shot-source.txt"
    if not record.is_file():
        problems.append("scripts/shot-source.txt is missing: run scripts/make-shots.sh")
        return
    recorded = {}
    for line in record.read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            digest, name = line.split(None, 1)
            recorded[name.strip()] = digest
    if not (GAME / ".git").exists():
        notes.append(f"SKIP the screenshots against the game's committed ones: {GAME} is not here")
        return
    try:
        current = {n: hashlib.sha256(subprocess.run(["git", "-C", str(GAME), "show", f"HEAD:{n}"], check=True,
                                                     capture_output=True).stdout).hexdigest() for n in recorded}
    except (OSError, subprocess.CalledProcessError) as error:
        problems.append(f"cannot read the game's committed screenshots from git: {error}")
        return
    changed = sorted(n for n in recorded if recorded[n] != current.get(n))
    if changed:
        problems.append("the site's screenshots were made from pictures the game no longer has at HEAD "
                        f"({', '.join(changed)}): run scripts/make-shots.sh, look, and commit")
    else:
        notes.append("the screenshots were made from the game's committed framed screenshots (HEAD)")


def check_game_urls(problems: list[str], notes: list[str]) -> None:
    links = GAME / "app" / "DuoAlley" / "Kit" / "Ads" / "AdsSettingsSection.swift"
    listing = GAME / "docs" / "APP-STORE-LISTING.md"
    if links.is_file():
        found = re.findall(r'privacyPolicy = URL\(string: "([^"]+)"\)', links.read_text(encoding="utf-8"))
        if found != [f"https://{DOMAIN}/privacy/"]:
            problems.append(f"the app's MoneyLinks.privacyPolicy is {found}, not https://{DOMAIN}/privacy/")
        else:
            notes.append("the privacy URL compiled into the app is this site's /privacy/")
    else:
        notes.append(f"SKIP the app's privacy URL: {links} is not here")
    if listing.is_file():
        text = listing.read_text(encoding="utf-8")
        for field, want in (("Support URL", f"https://{DOMAIN}/support/"), ("Marketing URL", f"https://{DOMAIN}"),
                            ("Privacy Policy URL", f"https://{DOMAIN}/privacy/")):
            row = re.search(r"^\|\s*" + re.escape(field) + r"\s*\|\s*`([^`]+)`", text, re.M)
            if not row or row.group(1) != want:
                problems.append(f"docs/APP-STORE-LISTING.md's {field} is {row.group(1) if row else None!r}, not {want}")
        notes.append("the listing's Support, Marketing and Privacy Policy URLs are this site's")
    else:
        notes.append(f"SKIP the listing's URLs: {listing} is not here")


def self_test() -> list[str]:
    tm = "S" + "kee"
    caught = {
        "trademark": [tm + "-Ball", tm.lower() + "ball", tm + " Ball", tm.upper() + "BALL", tm + "Boost", "an " + tm.lower()],
        "owners": ["Bay " + "Tek", "bay" + "tek", "Dimensional " + "Branding", "Ocean " + "Media", "Scope" + "ly",
                   "Big " + "Cave", "Skill" + "z", "Free" + "verse", "Ball " + "Master"],
        "pop": ["Pop-A-" + "Shot", "pop a " + "shot"],
        "league": ["the N" + "BA finals", "a W" + "N" + "BA star", "NC" + "AA bracket", "FI" + "FA rules",
                   "a UE" + "FA night", "an M" + "LS club"],
        "phrase": ["He's on " + "fire!", "he\u2019s on " + "fire"],
        "apps": ["like crater" + "gut", "muta" + "bloom's lesson", "Turf" + "storm", "wen" + "dra", "where" + "isit",
                 "Half " + "Court Duo", "half" + "court" + " duo", "Duo Shoot" + "out", "duo" + "shootout-website"],
    }
    missed = ["ABBA", "nbattery", "unbalanced", "HTML", "on fire", "a mutable bloom", "cratered", "skeleton",
              "a sketch", "whisked", "stormy turf", "a bowling alley", "a penalty shootout", NAME,
              "duoalley.com", "hingealley.com", "ball masters' guild", "big caves", "an ocean of media"]
    problems = []
    for group, needles in caught.items():
        for needle in needles:
            if not any(p.search(needle) for p, _ in PROTECTED):
                problems.append(f"self-test: no pattern catches {needle!r} ({group})")
    for text in missed:
        for p, why in PROTECTED:
            if p.search(text):
                problems.append(f"self-test: {text!r} is caught as {why}, and should not be")
    for needle in ["an em \u2014 dash", "1\u20132", "&m" + "dash;", "&n" + "dash;", "&#82" + "12;", "&#x20" + "13;"]:
        if not DASH.search(needle):
            problems.append(f"self-test: the dash pattern misses {needle!r}")
    if DASH.search("a hyphen-minus is fine, and &middot; too"):
        problems.append("self-test: the dash pattern catches a hyphen")
    for needle in ["Duo" + " Alley", "DUO" + " ALLEY", "duo" + "  alley"]:
        if not OLD_NAME.search(needle):
            problems.append(f"self-test: the former-name pattern misses {needle!r}")
    for text in ["duoalley.com", "hingealley.com", "app/DuoAlley/AppIcon.icon", "therealcreynold/duo" + "-alley", NAME, "Daily Alley"]:
        if OLD_NAME.search(text):
            problems.append(f"self-test: the former-name pattern catches {text!r}")
    for needle in ["a perfect match", "swipe right", "dating", "date night", "Matched!", "find your soulmate",
                   "It's a match", "matchmaking"]:
        if not DATING.search(needle):
            problems.append(f"self-test: the dating pattern misses {needle!r}")
    for text in ["Daily Alley, new at midnight UTC", "the date at the top", "a single ball", "Pass &amp; Play game",
                 "it hops the hinge", "Hinge parallax", "updated",
                 "Pass &amp; Play matches are never posted", "a two player match"]:
        if DATING.search(text):
            problems.append(f"self-test: the dating pattern catches {text!r}")
    if DEVICE.search(DEVICE_ALLOWED.sub("", "Designed for iPhone Duo")):
        problems.append("self-test: the allowed platform statement is refused")
    if not DEVICE.search(DEVICE_ALLOWED.sub("", "the iPhone Duo game")):
        problems.append("self-test: the device's name in prose is not caught")
    for needle in ["$2.99", "\u20ac3", "\u00a3 2", "USD 2.99", "2.99 USD"]:
        if not PRICE.search(needle):
            problems.append(f"self-test: the price pattern misses {needle!r}")
    for text in ["45 seconds", "the 100s", "a price shown by the App Store", "pub-5706069574815967"]:
        if PRICE.search(text):
            problems.append(f"self-test: the price pattern catches {text!r}")
    for needle in ["in 2027", "this spring", "by December"]:
        if not DATE.search(needle):
            problems.append(f"self-test: the date pattern misses {needle!r}")
    if DATE.search("Coming to the App Store. Stand it up like a laptop. Nine balls, 45 seconds, 270."):
        problems.append("self-test: the date pattern catches the page's own words")
    return problems


def main() -> int:
    problems = self_test()
    if "--self-test" in sys.argv:
        for p in problems:
            print(f"FAIL {p}")
        print("self-test: " + ("failed" if problems else "clean"))
        return 1 if problems else 0
    notes: list[str] = []
    check_words(problems)
    check_published(problems)
    check_pages(problems)
    check_contracts(problems)
    check_policy(problems, notes)
    check_icon_source(problems, notes)
    check_shot_source(problems, notes)
    check_game_urls(problems, notes)
    if "--require-game" in sys.argv:
        # Release gating: a missing game repository is a failure, never a skipped comparison.
        problems.extend(f"--require-game: {n}" for n in notes if n.startswith("SKIP"))
    for n in notes:
        print(f"NOTE {n}")
    for p in problems:
        print(f"FAIL {p}")
    print("lint-site: " + (f"{len(problems)} problem(s)" if problems else "clean"))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
