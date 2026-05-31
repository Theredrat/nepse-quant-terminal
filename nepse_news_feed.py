"""
nepse_news_feed.py
Fetches latest NEPSE news from ShareSansar and Merolagani.
Returns a list of story dicts compatible with dashboard_tui.py news format.

Usage:
    from nepse_news_feed import fetch_news
    stories = fetch_news()   # returns list of dicts

Each dict has:
    url, canonical_headline, summary, source, published
"""

import re
import json
from datetime import datetime
from pathlib import Path

CACHE_FILE = Path("_data/news_cache.json")
CACHE_MAX_AGE_MINUTES = 15

# ── helpers ───────────────────────────────────────────────────────────────────

def _get(url, timeout=8):
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""

def _strip_tags(html):
    return re.sub(r"<[^>]+>", " ", html).strip()

def _clean(text):
    text = re.sub(r"\s+", " ", text).strip()
    return text[:200] if text else ""

# ── scrapers ──────────────────────────────────────────────────────────────────

def _fetch_sharesansar():
    stories = []
    html = _get("https://www.sharesansar.com/news-page")
    if not html:
        return stories
    # Find news items — look for anchor tags with news headlines
    pattern = r'<a[^>]+href=["\']([^"\']*sharesansar\.com/[^"\']*)["\'][^>]*>(.*?)</a>'
    matches = re.findall(pattern, html, re.DOTALL)
    seen = set()
    for url, title in matches:
        title = _clean(_strip_tags(title))
        if len(title) < 20:
            continue
        if title in seen:
            continue
        # filter out nav links
        if any(x in title.lower() for x in ["login", "register", "home", "about", "contact", "menu"]):
            continue
        seen.add(title)
        stories.append({
            "url": url if url.startswith("http") else f"https://www.sharesansar.com{url}",
            "canonical_headline": title,
            "summary": title,
            "_translated": title,
            "source": "ShareSansar",
            "published": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        if len(stories) >= 10:
            break
    return stories

def _fetch_merolagani():
    stories = []
    html = _get("https://merolagani.com/NewsList.aspx")
    if not html:
        return stories
    pattern = r'<a[^>]+href=["\']([^"\']*merolagani\.com/[^"\']*NewsDetail[^"\']*)["\'][^>]*>(.*?)</a>'
    matches = re.findall(pattern, html, re.DOTALL)
    seen = set()
    for url, title in matches:
        title = _clean(_strip_tags(title))
        if len(title) < 20:
            continue
        if title in seen:
            continue
        seen.add(title)
        stories.append({
            "url": url if url.startswith("http") else f"https://merolagani.com{url}",
            "canonical_headline": title,
            "summary": title,
            "_translated": title,
            "source": "Merolagani",
            "published": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        if len(stories) >= 10:
            break
    return stories

def _fetch_nepse_notices():
    """NEPSE official notices from nepalstock.com"""
    stories = []
    html = _get("https://nepalstock.com/news")
    if not html:
        return stories
    pattern = r'<a[^>]+href=["\']([^"\']*)["\'][^>]*class=["\'][^"\']*news[^"\']*["\'][^>]*>(.*?)</a>'
    matches = re.findall(pattern, html, re.DOTALL)
    seen = set()
    for url, title in matches:
        title = _clean(_strip_tags(title))
        if len(title) < 15:
            continue
        if title in seen:
            continue
        seen.add(title)
        stories.append({
            "url": url if url.startswith("http") else f"https://nepalstock.com{url}",
            "canonical_headline": title,
            "summary": title,
            "_translated": title,
            "source": "NEPSE",
            "published": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        if len(stories) >= 5:
            break
    return stories

# ── cache ─────────────────────────────────────────────────────────────────────

def _load_cache():
    try:
        if CACHE_FILE.exists():
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            age = (datetime.now() - datetime.fromisoformat(data["fetched_at"])).total_seconds() / 60
            if age < CACHE_MAX_AGE_MINUTES:
                return data["stories"]
    except Exception:
        pass
    return None

def _save_cache(stories):
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps({
            "fetched_at": datetime.now().isoformat(),
            "stories": stories
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

# ── public API ────────────────────────────────────────────────────────────────

def fetch_news(force_refresh=False):
    """
    Returns list of story dicts. Uses cache (15 min) to avoid hammering sites.
    Each dict: url, canonical_headline, summary, _translated, source, published
    """
    if not force_refresh:
        cached = _load_cache()
        if cached:
            return cached

    stories = []
    stories.extend(_fetch_sharesansar())
    stories.extend(_fetch_merolagani())
    stories.extend(_fetch_nepse_notices())

    if stories:
        _save_cache(stories)

    return stories

# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Fetching NEPSE news...")
    news = fetch_news(force_refresh=True)
    print(f"Found {len(news)} stories\n")
    for i, s in enumerate(news[:10], 1):
        print(f"{i:2}. [{s['source']}] {s['canonical_headline']}")
        print(f"    {s['url']}")
        print()
