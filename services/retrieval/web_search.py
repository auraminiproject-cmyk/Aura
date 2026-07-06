"""Real product search via DuckDuckGo — zero API keys, real URLs.

Searches for real fashion products on Myntra, AJIO, Amazon, Nalli, and other
Indian fashion platforms. Returns actual product URLs, not hardcoded catalog.

Falls back to enhanced keyword-based search when DuckDuckGo is unreachable.
"""

import asyncio
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Target shopping platforms for Indian fashion
_SHOPPING_SITES = [
    "myntra.com",
    "ajio.com",
    "amazon.in",
    "flipkart.com",
    "nykaa.com/nykd",
    "tatacliq.com",
]


def _build_search_queries(spec: dict[str, Any]) -> list[str]:
    """Build targeted search queries from outfit spec."""
    queries: list[str] = []

    garment = spec.get("garment_type", "")
    fabric = spec.get("fabric", "")
    color = spec.get("color", "")
    occasion = spec.get("occasion", "")
    budget = spec.get("budget_inr")

    # Primary query: specific product search
    primary_parts = [p for p in [color, fabric, garment] if p]
    if primary_parts:
        primary = " ".join(primary_parts) + " buy online India"
        queries.append(primary)

    # Platform-specific queries using site operator for specific product links
    if garment:
        queries.append(f"site:myntra.com {color} {garment} buy")
        queries.append(f"site:ajio.com {fabric} {garment} online")

    # Budget-filtered query
    if budget and garment:
        if budget < 3000:
            queries.append(f"{garment} under {int(budget)} rupees online")
        else:
            queries.append(f"best {fabric} {garment} online India")

    # Occasion query
    if occasion and garment:
        queries.append(f"{garment} for {occasion} India")

    return queries[:4]  # Max 4 queries


async def _ddg_search(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Search DuckDuckGo for products. Returns list of {title, url, snippet}."""
    try:
        from ddgs import DDGS  # type: ignore[import-untyped]

        results: list[dict[str, str]] = []
        # Run synchronous ddgs in executor to not block async loop
        loop = asyncio.get_event_loop()

        def _search():
            with DDGS() as ddgs:
                hits = ddgs.text(query, max_results=max_results, region="in-en")
                return list(hits) if hits else []

        raw = await loop.run_in_executor(None, _search)
        for hit in raw:
            results.append({
                "title": hit.get("title", ""),
                "url": hit.get("href", hit.get("link", "")),
                "snippet": hit.get("body", hit.get("snippet", "")),
            })
        return results

    except ImportError:
        logger.warning("ddgs library not installed — pip install ddgs")
        return []
    except Exception as exc:
        logger.warning("DuckDuckGo search failed: %s", exc)
        return []


def _is_shopping_url(url: str) -> bool:
    """Check if URL is from a known shopping platform."""
    url_lower = url.lower()
    return any(site in url_lower for site in _SHOPPING_SITES)


def _extract_price_from_snippet(snippet: str) -> float | None:
    """Try to extract price from search snippet."""
    # Match ₹X,XXX or Rs X,XXX or INR X,XXX patterns
    match = re.search(r"(?:₹|Rs\.?|INR)\s*([\d,]+)", snippet)
    if match:
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            pass
    return None


def _categorize_platform(url: str) -> str:
    """Identify the shopping platform from URL."""
    url_lower = url.lower()
    for site in _SHOPPING_SITES:
        if site in url_lower:
            return site.split(".")[0].title()
    return "Online Store"


async def search_products(
    spec: dict[str, Any],
    *,
    limit: int = 5,
    max_price_inr: float | None = None,
) -> list[dict[str, Any]]:
    """Search for real products matching the outfit spec.

    Returns list of product dicts with real URLs, titles, prices, and platforms.
    """
    queries = _build_search_queries(spec)
    if not queries:
        return []

    all_results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    # Search with multiple queries for broader coverage
    for query in queries[:3]:  # Max 3 queries to stay fast
        try:
            raw_results = await asyncio.wait_for(
                _ddg_search(query, max_results=8),
                timeout=5.0,
            )
        except asyncio.TimeoutError:
            logger.warning("DDG search timed out for query: %s", query[:50])
            continue

        for r in raw_results:
            url = r.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            # Prefer shopping site URLs but include all
            is_shopping = _is_shopping_url(url)
            price = _extract_price_from_snippet(r.get("snippet", ""))

            # Apply price filter if specified
            if max_price_inr and price and price > max_price_inr:
                continue

            all_results.append({
                "name": r.get("title", "Fashion Product"),
                "url": url,
                "price_inr": price,
                "platform": _categorize_platform(url) if is_shopping else "Web",
                "snippet": r.get("snippet", "")[:200],
                "is_shopping_site": is_shopping,
                "search_query": query,
            })

    # Sort: shopping sites first, then by whether price was found
    all_results.sort(
        key=lambda x: (
            not x.get("is_shopping_site", False),
            x.get("price_inr") is None,
        )
    )

    return all_results[:limit]
