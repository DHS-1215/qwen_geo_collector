from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


GeoMode = Literal[
    "quick",
    "expert",
]

GeoTaskStatus = Literal[
    "success",
    "failed",
    "running",
]

GeoAcquisitionStatus = Literal[
    "success",
    "partial_success",
    "failed",
    "risk_control",
    "not_supported",
]

GeoValidationStatus = Literal[
    "PASS",
    "PASS_WITH_WARNINGS",
    "FAIL",
    "NOT_APPLICABLE",
]

GeoSourceCollectionStatus = Literal[
    "success",
    "partial_success",
    "failed",
    "not_supported",
]


class GeoPackageCapabilities(BaseModel):
    supports_sources: bool = True
    supports_multiple_modes: bool = True
    supports_screenshot: bool = False


class GeoPackageManifest(BaseModel):
    schema_version: Literal[
        "geo_package_v1"
    ] = "geo_package_v1"

    geo_batch_version: Literal[
        "geo_batch_v1"
    ] = "geo_batch_v1"

    platform_code: Literal[
        "qwen"
    ] = "qwen"

    platform_name: str = "千问"

    product_id: str
    product_name: str
    batch_id: str
    collector_version: str

    status: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    capabilities: GeoPackageCapabilities = Field(
        default_factory=GeoPackageCapabilities
    )

    # 中央 schema 允许额外字段。
    # 保留数量和文件列表，方便 Qwen 自校验。
    task_count: int = Field(
        default=0,
        ge=0,
    )

    answer_count: int = Field(
        default=0,
        ge=0,
    )

    source_count: int = Field(
        default=0,
        ge=0,
    )

    files: list[str] = Field(
        default_factory=list
    )


class GeoPackageTask(BaseModel):
    task_id: str
    question_id: str
    question: str

    mode_code: GeoMode
    task_status: GeoTaskStatus

    error_code: str | None = None
    error_message: str | None = None


class GeoPackageAnswer(BaseModel):
    answer_id: str
    task_id: str

    question_id: str
    mode_code: GeoMode

    question_text: str

    answer_text_raw: str | None
    answer_text_clean: str | None

    acquisition_status: GeoAcquisitionStatus
    validation_status: GeoValidationStatus

    is_complete: bool

    source_collection_status: (
        GeoSourceCollectionStatus
    )

    source_count_raw: int = Field(
        ge=0
    )

    screenshot_path: str | None = None

    collected_at: datetime

    platform_meta_json: dict[
        str,
        Any,
    ] = Field(
        default_factory=dict
    )


class GeoPackageSource(BaseModel):
    occurrence_id: str

    answer_id: str

    source_order: int = Field(
        ge=1
    )

    source_title_raw: str | None = None
    source_site_name_raw: str | None = None

    source_url_raw: str

    source_snippet: str | None = None

    is_duplicate_in_answer: bool = False
