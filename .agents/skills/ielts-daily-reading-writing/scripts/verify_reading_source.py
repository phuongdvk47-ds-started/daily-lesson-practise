#!/usr/bin/env python3
"""Verify that a proposed reading source URL is reachable and plausibly usable.

Usage:
  python scripts/verify_reading_source.py https://example.org/article

This script performs a lightweight HEAD/GET check, follows redirects, detects
common error statuses and soft-404 titles, and prints a concise report. It does
not validate copyright/license status; the agent must still check reuse rights.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser


class TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag: str):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str):
        if self.in_title:
            self.title_parts.append(data.strip())

    @property
    def title(self) -> str:
        return " ".join(part for part in self.title_parts if part).strip()


def fetch(url: str, timeout: int = 15) -> tuple[int, str, str, str]:
    headers = {"User-Agent": "Mozilla/5.0 IELTSDailySourceVerifier/1.0"}
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        final_url = resp.geturl()
        status = int(getattr(resp, "status", resp.getcode()))
        ctype = resp.headers.get("content-type", "")
        raw = resp.read(200000)
    text = raw.decode("utf-8", errors="replace")
    parser = TitleParser()
    parser.feed(text[:50000])
    return status, final_url, ctype, parser.title


def looks_like_soft_error(title: str, final_url: str) -> bool:
    haystack = f"{title} {final_url}".lower()
    patterns = [
        r"404", r"not found", r"page not found", r"access denied", r"forbidden",
        r"login", r"sign in", r"subscribe", r"error", r"không tìm thấy",
    ]
    return any(re.search(p, haystack) for p in patterns)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()
    try:
        status, final_url, ctype, title = fetch(args.url)
    except urllib.error.HTTPError as exc:
        print(f"FAIL\tstatus={exc.code}\turl={args.url}\treason={exc.reason}")
        return 2
    except Exception as exc:
        print(f"FAIL\turl={args.url}\terror={type(exc).__name__}: {exc}")
        return 2

    if status >= 400 or looks_like_soft_error(title, final_url):
        print(f"FAIL\tstatus={status}\tfinal_url={final_url}\ttitle={title!r}\tcontent_type={ctype}")
        return 2
    print(f"OK\tstatus={status}\tfinal_url={final_url}\ttitle={title!r}\tcontent_type={ctype}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
