#!/usr/bin/env python3
"""Robots policy regression tests. Run from engine-v2/: python3 tests/test_robots_policy.py."""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import common  # noqa: E402


def reset():
    common._ROBOTS_CACHE.clear()
    common.ROBOTS_FETCH_FAILURES.clear()


def main():
    reset()
    original_fetch = common.fetch_text
    try:
        common.fetch_text = lambda url, timeout=10: (_ for _ in ()).throw(
            OSError("simulated robots.txt network failure"))
        assert common.robots_allowed("https://example.com/news/story") is False
        assert "example.com" in common.robots_fetch_failures()
        print("PASS: robots fetch failure denies collection (fail-closed)")

        reset()
        common.fetch_text = lambda url, timeout=10: (
            "User-agent: *\nDisallow: /private/\nAllow: /private/public/\n")
        assert common.robots_allowed("https://example.com/news/story") is True
        assert common.robots_allowed("https://example.com/private/story") is False
        assert common.robots_allowed("https://example.com/private/public/story") is True
        print("PASS: longest matching robots rule wins; Allow wins ties")

        assert common.robots_allowed("not a URL") is False
        assert common.robots_allowed("") is False
        print("PASS: malformed or hostless URLs are denied")
    finally:
        common.fetch_text = original_fetch
        reset()


if __name__ == "__main__":
    main()
