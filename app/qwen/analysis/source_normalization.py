from __future__ import annotations

from urllib.parse import (
    parse_qsl,
    urlencode,
    urlsplit,
    urlunsplit,
)


TRACKING_QUERY_KEYS = {
    "spm",
    "utm_campaign",
    "utm_content",
    "utm_medium",
    "utm_source",
    "utm_term",
}


def canonicalize_source_url(
    url: str,
) -> str:
    raw = url.strip()

    if not raw:
        return ""

    parsed = urlsplit(
        raw
    )

    scheme = (
        parsed.scheme.lower()
    )

    hostname = (
        parsed.hostname or ""
    ).lower()

    if not hostname:
        return raw

    port = parsed.port

    if (
        port is not None
        and not (
            scheme == "http"
            and port == 80
        )
        and not (
            scheme == "https"
            and port == 443
        )
    ):
        netloc = (
            f"{hostname}:{port}"
        )
    else:
        netloc = hostname

    path = parsed.path or "/"

    query_items = []

    for key, value in parse_qsl(
        parsed.query,
        keep_blank_values=True,
    ):
        normalized_key = (
            key.strip().lower()
        )

        if (
            normalized_key
            in TRACKING_QUERY_KEYS
        ):
            continue

        if normalized_key.startswith(
            "utm_"
        ):
            continue

        query_items.append(
            (
                key,
                value,
            )
        )

    query_items.sort()

    query = urlencode(
        query_items,
        doseq=True,
    )

    return urlunsplit(
        (
            scheme,
            netloc,
            path,
            query,
            "",
        )
    )


def extract_source_domain(
    url: str,
) -> str:
    canonical = (
        canonicalize_source_url(
            url
        )
    )

    if not canonical:
        return ""

    hostname = (
        urlsplit(
            canonical
        ).hostname
        or ""
    ).lower()

    if hostname.startswith(
        "www."
    ):
        hostname = hostname[4:]

    return hostname
