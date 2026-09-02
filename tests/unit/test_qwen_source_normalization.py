from __future__ import annotations

from app.qwen.analysis.source_normalization import (
    canonicalize_source_url,
    extract_source_domain,
)


def test_url_is_trimmed_and_normalized():
    result = canonicalize_source_url(
        " HTTPS://Example.COM/a "
    )

    assert (
        result
        == "https://example.com/a"
    )


def test_fragment_is_removed():
    result = canonicalize_source_url(
        (
            "https://example.com/a"
            "#section"
        )
    )

    assert (
        result
        == "https://example.com/a"
    )


def test_query_parameters_are_sorted():
    result = canonicalize_source_url(
        (
            "https://example.com/a"
            "?b=2&a=1"
        )
    )

    assert (
        result
        == (
            "https://example.com/a"
            "?a=1&b=2"
        )
    )


def test_tracking_parameters_are_removed():
    result = canonicalize_source_url(
        (
            "https://example.com/a"
            "?id=1"
            "&utm_source=qwen"
            "&spm=test"
        )
    )

    assert (
        result
        == (
            "https://example.com/a"
            "?id=1"
        )
    )


def test_default_https_port_is_removed():
    result = canonicalize_source_url(
        (
            "https://example.com:443/a"
        )
    )

    assert (
        result
        == "https://example.com/a"
    )


def test_non_default_port_is_kept():
    result = canonicalize_source_url(
        (
            "https://example.com:8443/a"
        )
    )

    assert (
        result
        == (
            "https://example.com:8443/a"
        )
    )


def test_empty_path_becomes_slash():
    result = canonicalize_source_url(
        "https://example.com"
    )

    assert (
        result
        == "https://example.com/"
    )


def test_domain_removes_www():
    result = extract_source_domain(
        (
            "https://www.people.com.cn/"
            "news/1"
        )
    )

    assert (
        result
        == "people.com.cn"
    )


def test_subdomain_is_preserved():
    result = extract_source_domain(
        (
            "https://health.people.com.cn/"
            "news/1"
        )
    )

    assert (
        result
        == "health.people.com.cn"
    )


def test_empty_url():
    assert (
        canonicalize_source_url("")
        == ""
    )

    assert (
        extract_source_domain("")
        == ""
    )
