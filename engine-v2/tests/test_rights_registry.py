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
                "source_enabled": True,
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
                "automated_processing_status": "pending",
                "automated_processing_scope": "",
                "automated_processing_evidence": "",
                "reviewed_at": date.today().isoformat(),
                "review_due_at": (date.today() + timedelta(days=30)).isoformat()
            }
        }
    }


def main():
    reg = registry()
    url = "https://www.example.com/news/story"

    assert rr.metadata_decision(url, reg)[0] is False
    assert rr.metadata_decision("https://unknown.example/news", reg)[0] is False
    assert rr.metadata_decision("ftp://example.com/news/story", reg)[0] is False
    assert rr.metadata_decision("https://user:pass@example.com/news/story", reg)[0] is False
    assert rr.page_metadata_decision(url, reg)[0] is False
    assert rr.body_decision(url, reg)[0] is False
    print("PASS: publisher metadata permission alone does not authorise automated processing")

    reg["publishers"]["example.com"].update({
        "automated_processing_status": "approved",
        "automated_processing_scope": "automated classification, extraction and study summaries",
        "automated_processing_evidence": "written permission AP-001"
    })
    assert rr.metadata_decision(url, reg)[0] is True
    assert rr.body_decision(url, reg)[0] is False
    reg["publishers"]["example.com"]["source_enabled"] = False
    assert rr.metadata_decision(url, reg)[0] is False
    reg["publishers"]["example.com"]["source_enabled"] = True
    print("PASS: application source activation is required in addition to rights approvals")
    print("PASS: automated processing needs its own explicit scope and evidence")

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

    filter_reg = registry()
    filter_reg["publishers"]["example.com"].update({
        "automated_processing_status": "approved",
        "automated_processing_scope": "automated classification and study summaries",
        "automated_processing_evidence": "written permission AP-002"
    })
    permitted, blocked = rr.filter_metadata_items([
        {"url": url, "title": "Permitted"},
        {"url": "https://unknown.example/story", "title": "Unmapped"}
    ], filter_reg)
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

    original_fetch = collector.common.fetch_text
    collector.common.fetch_text = lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("unapproved page metadata must not be fetched"))
    try:
        assert collector._resolve_one_title({
            "url": "https://www.tbsnews.net/news/example",
            "title": "Slug headline"
        }) == ""
    finally:
        collector.common.fetch_text = original_fetch
    print("PASS: collector does not fetch article pages to resolve titles without permission")

    kept = [{"url": "https://www.tbsnews.net/news/example", "title": "Test"}]
    ok, tried = collector.fetch_bodies_for_kept(kept)
    assert (ok, tried) == (0, 0)
    assert kept[0]["body_text"] == ""
    assert "rights registry" in kept[0]["body_error"]
    print("PASS: collector never fetches article bodies without a licence")

    # Production registry must deny every currently unreviewed known publisher.
    prod = rr.load_registry()
    assert rr.publisher_name("https://www.dainikazadi.net/news/example", prod) == "Dainik Azadi"
    assert rr.publisher_name("https://www.sangbad.net.bd/news/example", prod) == "The Sangbad"
    assert rr.metadata_decision("https://www.prothomalo.com/news/test", prod)[0] is False
    assert rr.body_decision("https://www.tbsnews.net/news/test", prod)[0] is False
    assert prod["publishers"]["dailyinqilab.com"]["automated_processing_status"] == "restricted"
    assert prod["publishers"]["risingbd.com"]["automated_processing_status"] == "restricted"
    assert rr.metadata_decision("https://www.dailyinqilab.com/news/test", prod)[0] is False
    assert rr.body_decision("https://www.risingbd.com/news/test", prod)[0] is False
    print("PASS: AI-crawler warning sources remain explicitly restricted")
    print("PASS: current candidate publishers remain disabled pending evidence")


if __name__ == "__main__":
    main()
