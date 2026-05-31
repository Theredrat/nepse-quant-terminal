"""
patch_tui_news.py
Replaces the dead NepalOSINT API fetch in dashboard_tui.py
with a ShareSansar RSS news feed — no API key needed.
Safe: only replaces _fetch_osint_stories(), nothing else touched.
"""
import ast, shutil, re
from pathlib import Path

SRC = Path("dashboard_tui.py")
BACKUP = Path("dashboard_tui_pre_news_patch.py")

# ── safety check ─────────────────────────────────────────────────────────────
src = SRC.read_text(encoding="utf-8")
ast.parse(src)          # must be valid before we touch it
print("Syntax OK (before)")

# ── backup ───────────────────────────────────────────────────────────────────
shutil.copy(SRC, BACKUP)
print(f"Backup created → {BACKUP.name}")

# ── the new function ─────────────────────────────────────────────────────────
NEW_FETCH = '''def _fetch_osint_stories(limit: int = 40) -> list[dict]:
    """Fetch latest stories from ShareSansar news feed (free, no API key)."""
    import urllib.request, html, re as _re, time as _time

    sources = [
        ("https://www.sharesansar.com/category/latest", "ShareSansar"),
        ("https://www.merolagani.com/NewsList.aspx",    "Merolagani"),
    ]

    stories: list[dict] = []
    seen: set[str] = set()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
    }

    # ── ShareSansar ──────────────────────────────────────────────────────────
    try:
        req = urllib.request.Request(sources[0][0], headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            page = resp.read().decode("utf-8", errors="replace")

        # extract news cards: <a href="/newsdetail/...">Title</a>
        pattern = r'href="(/newsdetail/([^"]{10,120}))"[^>]*>\s*([^<]{10,200})'
        for m in _re.finditer(pattern, page):
            slug  = m.group(2)
            title = html.unescape(m.group(3)).strip()
            url   = "https://www.sharesansar.com" + m.group(1)
            if slug in seen or not title:
                continue
            seen.add(slug)
            # severity heuristic
            low = title.lower()
            if any(w in low for w in ("crash", "suspend", "halt", "ban", "fraud", "scam")):
                sev = "high"
            elif any(w in low for w in ("dividend", "bonus", "agm", "ipo", "merger",
                                         "budget", "tax", "interest", "rate")):
                sev = "medium"
            else:
                sev = "low"
            stories.append({
                "_translated": title,
                "summary": title,
                "url": url,
                "severity": sev,
                "source": "ShareSansar",
                "published_at": "",
            })
            if len(stories) >= limit:
                break
    except Exception:
        pass

    # ── Merolagani ───────────────────────────────────────────────────────────
    if len(stories) < limit:
        try:
            req2 = urllib.request.Request(sources[1][0], headers=headers)
            with urllib.request.urlopen(req2, timeout=8) as resp2:
                page2 = resp2.read().decode("utf-8", errors="replace")

            pat2 = r'href="(/NewsDetail\.aspx\?[^"]{5,120})"[^>]*>\s*([^<]{10,200})'
            for m in _re.finditer(pat2, page2):
                title = html.unescape(m.group(2)).strip()
                url   = "https://www.merolagani.com" + m.group(1)
                key   = title[:40]
                if key in seen or not title:
                    continue
                seen.add(key)
                low = title.lower()
                if any(w in low for w in ("dividend", "bonus", "agm", "ipo",
                                           "budget", "tax", "interest", "rate")):
                    sev = "medium"
                else:
                    sev = "low"
                stories.append({
                    "_translated": title,
                    "summary": title,
                    "url": url,
                    "severity": sev,
                    "source": "Merolagani",
                    "published_at": "",
                })
                if len(stories) >= limit:
                    break
        except Exception:
            pass

    return stories[:limit]
'''

# ── find and replace the old function ────────────────────────────────────────
OLD_PAT = re.compile(
    r'def _fetch_osint_stories\(.*?\n(?=def |\nclass |\Z)',
    re.DOTALL
)

match = OLD_PAT.search(src)
if not match:
    print("ERROR: could not locate _fetch_osint_stories() in dashboard_tui.py")
    print("       No changes made.")
    raise SystemExit(1)

new_src = src[:match.start()] + NEW_FETCH + "\n" + src[match.end():]

# ── validate ──────────────────────────────────────────────────────────────────
ast.parse(new_src)
print("Syntax OK (after)")

# ── write ─────────────────────────────────────────────────────────────────────
SRC.write_text(new_src, encoding="utf-8")
print("dashboard_tui.py updated — ShareSansar news feed wired in")
print()
print("The ticker + news panel will now show live headlines from:")
print("  • ShareSansar  (NEPSE market news)")
print("  • Merolagani   (company + sector news)")
print()
print("Stories marked severity=medium/high appear in the ticker.")
print("Run:  python dashboard_tui.py   to see them live.")
