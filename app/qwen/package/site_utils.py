from __future__ import annotations

from urllib.parse import urlparse


def source_site_name_from_url(
    url: str | None,
) -> str | None:
    if not url:
        return None

    try:
        host = urlparse(url).hostname
    except Exception:
        return None

    if not host:
        return None

    host = host.lower()

    if host.startswith("www."):
        host = host[4:]

    return host or None
