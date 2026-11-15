#!/usr/bin/env python3
"""Fail-closed publisher rights checks for Engine v2.

The registry is policy input, not a legal opinion. A source is denied by
default when its domain or permission evidence is missing. Public reachability
and robots.txt permission never override this registry.
"""
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parent
REGISTRY_PATH = BASE / "state" / "source_rights.json"


def load_registry(path=None):
    """Load the registry. Invalid or missing policy raises; callers must stop."""
    p = Path(path) if path else REGISTRY_PATH
    data = json.loads(p.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("publishers"), dict):
        raise ValueError("unsupported or malformed source rights registry")
    return data


def _host(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
            return ""
        if parsed.username or parsed.password:
            return ""
        host = parsed.hostname.lower().rstrip(".")
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def _record(url, registry=None):
    host = _host(url)
    if not host:
        return None, ""
    data = registry if registry is not None else load_registry()
    publishers = data.get("publishers", {})
    if host in publishers:
        return publishers[host], host
    matches = [(domain, record) for domain, record in publishers.items()
               if host.endswith("." + domain)]
    if matches:
        return max(matches, key=lambda pair: len(pair[0]))[1], host
    return None, host


def _not_expired(record):
    expiry = (record.get("expires_at") or "").strip()
    if not expiry:
        return True
    try:
        return date.fromisoformat(expiry) >= date.today()
    except ValueError:
        return False


def _has_evidence(record, scope_key, evidence_key):
    return bool((record.get(scope_key) or "").strip()
                and (record.get(evidence_key) or "").strip()
                and _not_expired(record))


def discovery_host_allowed(url, registry=None):
    data = registry if registry is not None else load_registry()
    host = _host(url)
    allowed = {str(x).lower().removeprefix("www.")
               for x in data.get("policy", {}).get("discovery_hosts", [])}
    return bool(host and host in allowed)


def metadata_decision(url, registry=None):
    record, host = _record(url, registry)
    if not host:
        return False, "invalid publisher URL"
    if not record:
        return False, "publisher domain is not mapped in rights registry"
    if record.get("metadata_status") != "approved":
        return False, "publisher metadata permission is not approved"
    if not _has_evidence(record, "metadata_scope", "metadata_evidence"):
        return False, "metadata permission lacks scope, evidence or is expired"
    return True, "metadata permission approved"


def page_metadata_decision(url, registry=None):
    record, host = _record(url, registry)
    if not host:
        return False, "invalid publisher URL"
    if not record:
        return False, "publisher domain is not mapped in rights registry"
    if record.get("page_metadata_status") == "approved" and (
            record.get("page_metadata_scope") or "").strip() and (
            record.get("page_metadata_evidence") or "").strip() and _not_expired(record):
        return True, "page metadata permission approved"
    if body_decision(url, registry)[0]:
        return True, "licensed article-page processing"
    return False, "article-page metadata extraction is not approved"


def body_decision(url, registry=None):
    record, host = _record(url, registry)
    if not host:
        return False, "invalid publisher URL"
    if not record:
        return False, "publisher domain is not mapped in rights registry"
    if record.get("body_status") != "licensed":
        return False, "article-body licence is not approved"
    if not _has_evidence(record, "body_scope", "body_evidence"):
        return False, "article-body licence lacks scope, evidence or is expired"
    return True, "article-body licence approved"


def filter_metadata_items(items, registry=None):
    """Return (permitted_items, blocked_counts_by_publisher)."""
    permitted, blocked = [], {}
    for item in items:
        url = item.get("url") or ""
        allowed, reason = metadata_decision(url, registry)
        if allowed:
            permitted.append(item)
        else:
            record, host = _record(url, registry)
            publisher = (record or {}).get("publisher") or host or "invalid URL"
            blocked[publisher] = blocked.get(publisher, 0) + 1
    return permitted, blocked
