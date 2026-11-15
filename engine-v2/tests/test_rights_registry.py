#!/usr/bin/env python3
"""Publisher rights registry regression tests. Run from engine-v2/."""
import json
import sys
import tempfile
from pathlib import Path
from datetime import date, timedelta

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import rights_registry as rr  # noqa: E402


def registry():
    return {
        "version": 1,
        "policy": {"discovery_hosts": ["www.bing.com", "news.google.com"]},
        "publishers": {
            "example.com": {
                "publisher": "Example News",
                "metadata_status": "approved",
                "metadata_scope": "headline, canonical URL and publication date",
                "metadata_evidence": "https://example.com/terms",
                "page_metadata_status": "pending",
                "page_metadata_scope": "",
                "page_metadata_evidence": "",
                "body_status": "not_permitted",
                "body_scope": "",
                "body_evidence": "",
                "expires_at": "",
                "reviewed_at": date.today().isoformat(),
                "review_due_at": (date.today() + timedelta(days=30)).isoformat()
            }
        }
    }


def main():
    reg = registry()
    url = "https://www.example.com/news/story"

    assert rr.metadata_decision(url, reg)[0] is True
    assert rr.metadata_decision("https://unknown.example/news", reg)[0] is False
    assert rr.metadata_decision("ftp://example.com/news/story", reg)[0] is False
    assert rr.metadata_decision("https://user:pass@example.com/news/story", reg)[0] is False
    assert rr.page_metadata_decision(url, reg)[0] is False
    assert rr.body_decision(url, reg)[0] is False
    print("PASS: metadata permission does not imply article-page or body permission")

    reg["publishers"]["example.com"].update({
        "page_metadata_status": "approved",
        "page_metadata_scope": "canonical headline and publish date",
        "page_metadata_evidence": "https://example.com/terms"
    })
    assert rr.page_metadata_decision(url, reg)[0] is True
    print("PASS: page metadata requires its own evidence")

    reg["publishers"]["example.com"].update({
        "body_status": "licensed",
        "body_scope": "fetch, analyse and display up to 400 words with attribution",
        "body_evidence": "written licence agreement LIC-001"
    })
    assert rr.body_decision(url, reg)[0] is True
    print("PASS: body access requires licensed status, scope and evidence")

    reg["publishers"]["example.com"]["expires_at"] = (
        date.today() - timedelta(days=1)).isoformat()
    assert rr.body_decision(url, reg)[0] is False
    assert rr.metadata_decision(url, reg)[0] is False
    reg["publishers"]["example.com"]["expires_at"] = ""
    reg["publishers"]["example.com"]["review_due_at"] = (
        date.today() - timedelta(days=1)).isoformat()
    assert rr.body_decision(url, reg)[0] is False
    print("PASS: expired licences and overdue rights reviews are denied")

    permitted, blocked = rr.filter_metadata_items([
        {"url": url, "title": "Permitted"},
        {"url": "https://unknown.example/story", "title": "Unmapped"}
    ], registry())
    assert len(permitted) == 1 and permitted[0]["title"] == "Permitted"
    assert blocked.get("unknown.example") == 1
    print("PASS: metadata filter keeps only explicitly approved publisher records")

    assert rr.discovery_host_allowed("https://www.bing.com/news/search", registry())
    assert not rr.discovery_host_allowed("https://example.com/feed", registry())
    print("PASS: aggregator discovery host allowlist is separate from publisher rights")

    import step1_collect as collector
    report = {}
    assert collector._fetch_route(
        "https://www.prothomalo.com/feed", "Prothom Alo", report,
        "rss", {}) is None
    assert "blocked by rights registry" in report["Prothom Alo"]["status"]
    print("PASS: collector blocks direct publisher feeds until metadata approval")

    kept = [{"url": "https://www.tbsnews.net/news/example", "title": "Test"}]
    ok, tried = collector.fetch_bodies_for_kept(kept)
    assert (ok, tried) == (0, 0)
    assert kept[0]["body_text"] == ""
    assert "rights registry" in kept[0]["body_error"]
    print("PASS: collector never fetches article bodies without a licence")

    # Production registry must deny every currently unreviewed known publisher.
    prod = rr.load_registry()
    assert rr.metadata_decision("https://www.prothomalo.com/news/test", prod)[0] is False
    assert rr.body_decision("https://www.tbsnews.net/news/test", prod)[0] is False
    print("PASS: current candidate publishers remain disabled pending evidence")


if __name__ == "__main__":
    main()
