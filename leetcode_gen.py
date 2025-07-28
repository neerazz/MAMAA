#!/usr/bin/env python3
"""
LeetCode Scraper & Boilerplate Generator (GraphQL‑powered)
==========================================================

Behaviour (v2)
--------------
* **Always (re)generates** the solution file – if one already exists it is
  **over‑written** with the fresh template instead of being appended to.
* **Clickable path** printed after every run (works in most modern IDEs).
* **Verbose, structured logging** – see every major step: URL→slug, payload,
  response metadata, topic‑tag sanitisation, directory creation and file write.
* **Runtime log level control** – set `LOG_LEVEL=DEBUG` (or INFO/WARNING/ERROR)
  in your shell to adjust verbosity without touching the code.

Requirements: `requests`, `beautifulsoup4`
"""

from __future__ import annotations

import json
import logging
import os
import re
from html import unescape
from pathlib import Path
from typing import Optional, Tuple, List, Dict

import requests
from bs4 import BeautifulSoup

# ───────────────────────────────────────────────────────────
# CONFIGURATION
# ───────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Max chars of JSON we emit at DEBUG to avoid terminal spam
MAX_DEBUG_JSON = 800

# ───────────────────────────────────────────────────────────
# GRAPHQL CONSTANTS
# ───────────────────────────────────────────────────────────
_GRAPHQL_QUERY = """
query getQuestion($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    title
    content
    topicTags { name slug }
  }
}
"""

_HEADERS = {
    "Referer": "https://leetcode.com",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
}

# ───────────────────────────────────────────────────────────
# UTILITIES
# ───────────────────────────────────────────────────────────

def slug_from_url(url: str) -> Optional[str]:
    match = re.search(r"/problems/([^/]+)/", url)
    slug = match.group(1) if match else None
    logger.debug("Slug '%s' extracted from %s", slug, url)
    return slug


def html_to_plain_text(html: str) -> str:
    """Strip HTML to plain‑text for the problem description."""
    return unescape(BeautifulSoup(html, "html.parser").get_text("\n").strip())

# ───────────────────────────────────────────────────────────
# FETCH & PARSE
# ───────────────────────────────────────────────────────────

def get_problem_details(url: str) -> Tuple[Optional[str], ...]:
    slug = slug_from_url(url)
    if not slug:
        logger.error("Invalid LeetCode URL: %s", url)
        return (None,) * 5

    logger.info("📡 Fetching '%s'", slug)
    payload: Dict[str, object] = {"query": _GRAPHQL_QUERY, "variables": {"titleSlug": slug}}

    try:
        res = requests.post("https://leetcode.com/graphql", headers=_HEADERS, json=payload, timeout=10)
        res.raise_for_status()
    except requests.RequestException as exc:
        logger.error("GraphQL error: %s", exc)
        return (None,) * 5

    # Emit a truncated JSON preview at DEBUG level
    if logger.isEnabledFor(logging.DEBUG):
        preview = json.dumps(res.json())[:MAX_DEBUG_JSON]
        logger.debug("GraphQL response preview: %s…", preview)

    data = res.json()
    question = data.get("data", {}).get("question")
    if not question:
        logger.error("No question data for slug %s", slug)
        return (None,) * 5

    title: str = question["title"].strip()
    description = html_to_plain_text(question["content"])

    tag_names = [t["name"] for t in question.get("topicTags", [])]
    topic_dir = re.sub(r"[^\w\s-]", "", (tag_names[0] if tag_names else "general")).replace(" ", "_").lower()

    file_name = re.sub(r"[^\w\s-]", "", title).replace(" ", "_").lower() + ".py"

    words = title.split()
    method_name = words[0].lower() + "".join(w.capitalize() for w in words[1:])
    basic_snippet = f'''\
class Solution:
    def {method_name}(self):  # TODO: adjust parameters
        """
        Problem: {title}
        """
        # Your code here
        pass

# Example:
# s = Solution()
# print(s.{method_name}(/* args */))
'''
    return title, description, basic_snippet, file_name, topic_dir

# ───────────────────────────────────────────────────────────
# FILE OPERATIONS
# ───────────────────────────────────────────────────────────

def write_solution_file(abs_path: Path, title: str, desc: str, snippet: str, topic_dir: str, url: str) -> None:
    """(Re)write the solution file with fresh template."""
    try:
        with abs_path.open("w", encoding="utf-8") as f:
            f.write('"""\n')
            f.write(f"LeetCode Problem: {title}\n")
            f.write(f"URL: {url}\n\n")
            f.write(f"Topic: {topic_dir.replace('_', ' ').title()}\n\n")
            f.write("Description:\n")
            f.write(desc + "\n")
            f.write('"""\n\n')
            f.write(snippet)
        logger.info("✅ (Re)generated file: %s", abs_path)
    except OSError as exc:
        logger.error("Cannot write file %s: %s", abs_path, exc)


def create_solution_file(url: str) -> None:
    title, desc, snippet, fname, tdir = get_problem_details(url)
    if not all((title, desc, snippet, fname, tdir)):
        return

    topic_path = Path(tdir)
    topic_path.mkdir(parents=True, exist_ok=True)
    abs_path = (topic_path / fname).resolve()

    if abs_path.exists():
        logger.warning("↻ File exists – it will be overwritten: %s", abs_path)
    else:
        logger.info("📄 Creating new file: %s", abs_path)

    write_solution_file(abs_path, title, desc, snippet, tdir, url)
    # Print the absolute path so IDE terminals recognise it as a clickable link
    print(abs_path)

# ───────────────────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    PROBLEM_URLS = [
        "https://leetcode.com/problems/daily-temperatures/?envType=study-plan-v2&envId=leetcode-75",
    ]

    for link in PROBLEM_URLS:
        logger.info("\n—— Processing %s ——", link)
        create_solution_file(link)
