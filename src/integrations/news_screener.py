"""Negative news screening for AML/CFT compliance.

Scrapes major Indonesian media RSS feeds for mentions of entity names, then
classifies sentiment using lexicon-based rules (simple + offline).

Sources:
    - Kompas:    https://news.kompas.com/rss
    - Detik:     https://news.detik.com/rss
    - Tempo:     https://www.tempo.co/feed
    - Antara:    https://www.antaranews.com/rss/terkini.xml
    - CNN ID:    https://www.cnnindonesia.com/nasional/rss
"""
from __future__ import annotations

import re
import defusedxml.ElementTree as ET  # safe parser: RSS feeds are untrusted input
from dataclasses import dataclass
from typing import Optional

import httpx

from src.common.config import settings
from src.common.logger import get_logger

log = get_logger("integrations.news")

RSS_FEEDS = {
    "kompas":  "https://news.kompas.com/rss",
    "detik":   "https://news.detik.com/rss",
    "tempo":   "https://rss.tempo.co/nasional",
    "antara":  "https://www.antaranews.com/rss/terkini.xml",
    "cnn_id":  "https://www.cnnindonesia.com/nasional/rss",
}

CACHE_DIR = settings.app_data_dir / "news"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Negative-sentiment lexicon (Indonesian + adopted English terms commonly used in news)
NEGATIVE_KEYWORDS = {
    # Financial crime
    "korupsi", "suap", "gratifikasi", "fraud", "penipuan", "menipu",
    "money laundering", "pencucian uang", "tppu", "mafia",
    "investasi bodong", "investasi ilegal", "skema ponzi", "ponzi",
    # Criminal/terrorism
    "teroris", "terorisme", "pembunuhan", "perampokan", "pencurian",
    "narkoba", "narkotika", "sabu", "ekstasi", "kokain",
    # Sanctions/legal
    "tersangka", "buronan", "ditangkap", "diadili", "vonis", "hukuman",
    "dakwaan", "kpk", "ditahan", "diciduk",
    # Cybercrime
    "phising", "phishing", "scam", "rug pull", "hack", "diretas",
    # Sanctions
    "diblokir", "dibekukan", "sanksi", "ofac", "ppatk",
}


@dataclass
class NewsHit:
    source: str
    title: str
    link: str
    published: str
    snippet: str
    sentiment_score: float    # 0..1, higher = more negative
    matched_keywords: list[str]
    entity_query: str


# ============================================================
# RSS fetching + parsing
# ============================================================
def _fetch_feed(name: str, url: str, timeout: int = 12) -> list[dict]:
    """Return list of {title, link, description, pubDate} from a single feed."""
    items: list[dict] = []
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True,
                          headers={"User-Agent": "FinCrime-AI/0.1 (compliance research)"}) as c:
            r = c.get(url)
            r.raise_for_status()
            tree = ET.fromstring(r.content)
    except Exception as e:
        log.warning("news.fetch_failed", source=name, error=str(e))
        return items

    for item in tree.iter("item"):
        items.append({
            "title": (item.findtext("title") or "").strip(),
            "link": (item.findtext("link") or "").strip(),
            "description": (item.findtext("description") or "").strip(),
            "pubDate": (item.findtext("pubDate") or "").strip(),
        })
    log.debug("news.fetched", source=name, n=len(items))
    return items


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s)


def _sentiment_score(text: str) -> tuple[float, list[str]]:
    """Lexicon-based negative-sentiment score in [0, 1]."""
    if not text:
        return 0.0, []
    low = text.lower()
    matched = [kw for kw in NEGATIVE_KEYWORDS if kw in low]
    # Normalize: more matches = higher score, capped at 1.0
    score = min(1.0, len(matched) / 5.0)
    # Boost if very strong words appear
    strong = {"teroris", "korupsi", "tppu", "pencucian uang", "buronan", "ditangkap"}
    if any(s in matched for s in strong):
        score = min(1.0, score + 0.3)
    return round(score, 3), matched


def _name_matches(text: str, query: str) -> bool:
    """Case-insensitive substring match with simple word-boundary handling."""
    if not text or not query:
        return False
    return query.lower() in text.lower()


# ============================================================
# Public API
# ============================================================
def screen_entity(entity_name: str,
                  sources: Optional[list[str]] = None,
                  min_score: float = 0.0,
                  limit: int = 25) -> list[NewsHit]:
    """Scan recent news for mentions of `entity_name`. Returns ranked hits.

    Args:
        entity_name: e.g., "PT Maju Bersama" or "Budi Santoso"
        sources: list of feed names to scan (default: all)
        min_score: minimum sentiment score (0..1)
        limit: max items returned

    Returns hits sorted by sentiment_score desc.
    """
    sources = sources or list(RSS_FEEDS.keys())
    all_hits: list[NewsHit] = []
    for src in sources:
        url = RSS_FEEDS.get(src)
        if not url:
            continue
        items = _fetch_feed(src, url)
        for it in items:
            text = f"{it['title']} {_strip_html(it['description'])}"
            if not _name_matches(text, entity_name):
                continue
            score, kws = _sentiment_score(text)
            if score < min_score:
                continue
            all_hits.append(NewsHit(
                source=src,
                title=it["title"],
                link=it["link"],
                published=it["pubDate"],
                snippet=_strip_html(it["description"])[:240],
                sentiment_score=score,
                matched_keywords=kws,
                entity_query=entity_name,
            ))
    all_hits.sort(key=lambda h: -h.sentiment_score)
    log.info("news.screened", query=entity_name, total=len(all_hits),
             sources=len(sources))
    return all_hits[:limit]


def batch_screen(entity_names: list[str], min_score: float = 0.3) -> dict[str, list[NewsHit]]:
    """Screen multiple entities. Returns dict[name -> hits]."""
    out: dict[str, list[NewsHit]] = {}
    for name in entity_names:
        hits = screen_entity(name, min_score=min_score, limit=10)
        if hits:
            out[name] = hits
    return out
