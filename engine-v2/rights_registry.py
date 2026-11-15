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
_DEFAULT_REGISTRY = None


def load_registry(path=None):
    """Load the registry. Invalid or missing policy raises; callers must stop."""
    global _DEFAULT_REGISTRY
    if path is None and _DEFAULT_REGISTRY is not None:
        return _DEFAULT_REGISTRY
    p = Path(path) if path else REGISTRY_PATH
    data = json.loads(p.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("publishers"), dict):
        raise ValueError("unsupported or malformed source rights registry")
    if path is None:
        _DEFAULT_REGISTRY = data
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


def _review_current(record):
    """Require a dated review and a future review-due date for every approval."""
    reviewed = (record.get("reviewed_at") or "").strip()
    due = (record.get("review_due_at") or "").strip()
    try:
        reviewed_date = date.fromisoformat(reviewed)
        due_date = date.fromisoformat(due)
    except ValueError:
        return False
    today = date.today()
    if reviewed_date > today or due_date < today or due_date < reviewed_date:
        return False
    expiry = (record.get("expires_at") or "").strip()
    if expiry:
        try:
            if date.fromisoformat(expiry) < today:
                return False
        except ValueError:
            return False
    return True


def _has_evidence(record, scope_key, evidence_key):
    return bool((record.get(scope_key) or "").strip()
                and (record.get(evidence_key) or "").strip()
                and _review_current(record))


def discovery_host_allowed(url, registry=None):
    data = registry if registry is not None else load_registry()
    host = _host(url)
    allowed = {str(x).lower().removeprefix("www.")
               for x in data.get("policy", {}).get("discovery_hosts", [])}
    return bool(host and host in allowed)


def publisher_name(url, registry=None):
    """Return the reviewed registry label for a known domain, else empty."""
    record, host = _record(url, registry)
    if not host or not record:
        return ""
    return (record.get("publisher") or "").strip()


def metadata_decision(url, registry=None):
    record, host = _record(url, registry)
    if not host:
        return False, "invalid publisher URL"
    if not record:
        return False, "publisher domain is not mapped in rights registry"
    if record.get("source_enabled") is not True:
        return False, "publisher source is not enabled in the application rights ledger"
    if record.get("metadata_status") != "approved":
        return False, "publisher metadata permission is not approved"
    if not _has_evidence(record, "metadata_scope", "metadata_evidence"):
        return False, "metadata permission lacks scope, evidence or is expired"
    if record.get("automated_processing_status") != "approved" or not _has_evidence(
            record, "automated_processing_scope", "automated_processing_evidence"):
        return False, "automated processing permission is not approved with current scope/evidence"
    return True, "metadata and automated processing permissions approved"


def page_metadata_decision(url, registry=None):
    record, host = _record(url, registry)
    if not host:
        return False, "invalid publisher URL"
    if not record:
        return False, "publisher domain is not mapped in rights registry"
    if record.get("source_enabled") is not True:
        return False, "publisher source is not enabled in the application rights ledger"
    if record.get("page_metadata_status") == "approved" and (
            record.get("page_metadata_scope") or "").strip() and (
            record.get("page_metadata_evidence") or "").strip() and _review_current(record) and (
            record.get("automated_processing_status") == "approved") and _has_evidence(
            record, "automated_processing_scope", "automated_processing_evidence"):
        return True, "page metadata and automated processing permissions approved"
    if body_decision(url, registry)[0]:
        return True, "licensed article-page processing"
    return False, "article-page metadata extraction is not approved"


def body_decision(url, registry=None):
    record, host = _record(url, registry)
    if not host:
        return False, "invalid publisher URL"
    if not record:
        return False, "publisher domain is not mapped in rights registry"
    if record.get("source_enabled") is not True:
        return False, "publisher source is not enabled in the application rights ledger"
    if record.get("body_status") != "licensed":
        return False, "article-body licence is not approved"
    if not _has_evidence(record, "body_scope", "body_evidence"):
        return False, "article-body licence lacks scope, evidence or is expired"
    if record.get("automated_processing_status") != "approved" or not _has_evidence(
            record, "automated_processing_scope", "automated_processing_evidence"):
        return False, "automated processing permission is not approved with current scope/evidence"
    return True, "article-body and automated processing permissions approved"


def filter_metadata_items(items, registry=None):
    """Return (permitted_items, blocked_counts_by_publisher)."""
    permitted, blocked = [], {}
    for item in items:
        url = item.get("url") or ""
        allowed, reason = metadata_decision(url, registry)
        if allowed:
            clean = dict(item)
            # RSS descriptions are article excerpts, not basic bibliographic
            # metadata. No separate excerpt permission is represented here,
            # so do not retain or process them under a headline-only grant.
            clean["summary"] = ""
            permitted.append(clean)
        else:
            record, host = _record(url, registry)
            publisher = (record or {}).get("publisher") or host or "invalid URL"
            blocked[publisher] = blocked.get(publisher, 0) + 1
    return permitted, blocked
