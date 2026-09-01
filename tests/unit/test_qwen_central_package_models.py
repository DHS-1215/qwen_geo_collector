from __future__ import annotations

from app.qwen.package.central_models import (
    GeoPackageCapabilities,
    GeoPackageManifest,
)


def test_central_manifest_uses_geo_package_contract():
    manifest = GeoPackageManifest(
        product_id="hongmao",
        product_name="鸿茅药酒",
        batch_id="qwen-test-001",
        collector_version="w4.1",
    )

    assert (
        manifest.schema_version
        == "geo_package_v1"
    )

    assert (
        manifest.geo_batch_version
        == "geo_batch_v1"
    )

    assert (
        manifest.platform_code
        == "qwen"
    )

    assert (
        manifest.platform_name
        == "千问"
    )

    assert (
        manifest.product_id
        == "hongmao"
    )

    assert (
        manifest.capabilities
        == GeoPackageCapabilities(
            supports_sources=True,
            supports_multiple_modes=True,
            supports_screenshot=False,
        )
    )
