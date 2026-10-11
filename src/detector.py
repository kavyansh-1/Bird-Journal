"""Bird call detection using BirdNET, running fully offline.

BirdNET (https://github.com/birdnet-team/BirdNET-Analyzer) is an open-source
neural network trained to identify thousands of bird species from audio.
The `birdnet` pip package downloads the model weights ONCE (from Zenodo) and
caches them; after that no internet is needed.

We use library="litert" so TensorFlow is not required - a much lighter
install that also works on a Raspberry Pi.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Detection:
    common_name: str
    scientific_name: str
    confidence: float
    start_s: float
    end_s: float


def _load_models(use_geo: bool):
    try:
        import birdnet  # type: ignore
    except ImportError as e:
        raise SystemExit(
            "BirdNET is not installed. Run: pip install -r requirements.txt"
        ) from e
    acoustic = birdnet.load("acoustic", "2.4", "tf", library="litert")
    geo = birdnet.load("geo", "2.4", "tf", library="litert") if use_geo else None
    return acoustic, geo


def detect(
    audio_path: str | Path,
    lat: float | None = None,
    lon: float | None = None,
    week: int | None = None,
    min_conf: float = 0.4,
    models=None,
) -> list[Detection]:
    """Run BirdNET on an audio file and return detections.

    If lat/lon are given, BirdNET's geo model builds a list of species that
    plausibly occur at that place and week, and everything else is ignored.
    This noticeably cuts false positives (no penguins in Punjab).

    `models` lets tests inject a fake (acoustic, geo) pair.
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(audio_path)

    use_geo = lat is not None and lon is not None
    acoustic, geo = models if models is not None else _load_models(use_geo)

    species_filter = None
    if geo is not None and use_geo:
        species_filter = geo.predict(lat, lon, week=week, min_confidence=0.03).to_set()

    kwargs = {"top_k": 5, "default_confidence_threshold": min_conf}
    if species_filter:
        kwargs["custom_species_list"] = species_filter

    preds = acoustic.predict(str(audio_path), **kwargs)
    detections = list(_iter_rows(preds))
    detections = [d for d in detections if d.confidence >= min_conf]
    detections.sort(key=lambda d: d.start_s)
    return detections


def _iter_rows(preds):
    """Turn BirdNET's result table into Detection objects.

    `species_name` looks like "Scientific name_Common name".
    """
    df = preds.to_dataframe()
    for _, r in df.iterrows():
        species = str(r["species_name"])
        sci, _, common = species.partition("_")
        yield Detection(
            common_name=common or sci,
            scientific_name=sci,
            confidence=float(r["confidence"]),
            start_s=float(r["start_time"]),
            end_s=float(r["end_time"]),
        )


def summarise(detections: list[Detection]) -> list[dict]:
    """Collapse per-clip detections into one row per species."""
    by_species: dict[str, dict] = {}
    for d in detections:
        s = by_species.setdefault(
            d.common_name,
            {
                "common_name": d.common_name,
                "scientific_name": d.scientific_name,
                "count": 0,
                "best_confidence": 0.0,
                "first_heard_s": d.start_s,
            },
        )
        s["count"] += 1
        s["best_confidence"] = max(s["best_confidence"], d.confidence)
        s["first_heard_s"] = min(s["first_heard_s"], d.start_s)
    return sorted(by_species.values(), key=lambda r: -r["count"])
