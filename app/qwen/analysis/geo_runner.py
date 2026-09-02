from __future__ import annotations

import inspect
from pathlib import Path
from typing import Sequence

from app.qwen.analysis.geo_metrics import (
    build_geo_metrics,
)
from app.qwen.analysis.geo_models import (
    GeoAnalysisBundle,
)
from app.qwen.analysis.models import (
    MentionTarget,
)
from app.qwen.analysis.runner import (
    run_mention_analysis,
)
from app.qwen.analysis.sentiment import (
    SentimentClassifier,
)
from app.qwen.analysis.sentiment_runner import (
    run_sentiment_analysis,
)
from app.qwen.analysis.source_runner import (
    run_source_analysis,
)


async def run_geo_analysis(
    batch_dir: str | Path,
    targets: Sequence[MentionTarget],
    classifier: SentimentClassifier,
) -> GeoAnalysisBundle:
    target_list = list(
        targets
    )

    if not target_list:
        raise ValueError(
            "at least one target is required"
        )

    target_ids = [
        target.target_id
        for target in target_list
    ]

    if len(
        target_ids
    ) != len(
        set(target_ids)
    ):
        raise ValueError(
            "duplicate target_id"
        )

    mention = run_mention_analysis(
        batch_dir,
        target_list,
    )

    sentiment_value = (
        run_sentiment_analysis(
            batch_dir,
            target_list,
            classifier,
        )
    )

    if inspect.isawaitable(
        sentiment_value
    ):
        sentiment = await sentiment_value
    else:
        sentiment = sentiment_value

    sources = run_source_analysis(
        batch_dir
    )

    metrics = build_geo_metrics(
        mention=mention,
        sentiment=sentiment,
        sources=sources,
    )

    return GeoAnalysisBundle(
        mention=mention,
        sentiment=sentiment,
        sources=sources,
        metrics=metrics,
    )
