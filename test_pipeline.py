"""Offline smoke test: fakes BirdNET so the rest of the pipeline can be checked.

Run:  python test_pipeline.py
"""

import tempfile
from pathlib import Path

import pandas as pd

import detector
import journal


class FakePreds:
    def to_dataframe(self):
        return pd.DataFrame(
            {
                "input": ["walk.wav"] * 4,
                "start_time": [0.0, 3.0, 6.0, 9.0],
                "end_time": [3.0, 6.0, 9.0, 12.0],
                "species_name": [
                    "Psilopogon haemacephalus_Coppersmith Barbet",
                    "Psilopogon haemacephalus_Coppersmith Barbet",
                    "Acridotheres tristis_Common Myna",
                    "Copsychus saularis_Oriental Magpie-Robin",
                ],
                "confidence": [0.91, 0.62, 0.77, 0.45],
            }
        )


class FakeAcoustic:
    def predict(self, path, **kwargs):
        self.kwargs = kwargs
        return FakePreds()


class FakeGeoResult:
    def to_set(self):
        return {"Psilopogon haemacephalus_Coppersmith Barbet"}


class FakeGeo:
    def predict(self, lat, lon, week=None, min_confidence=0.03):
        return FakeGeoResult()


def main():
    with tempfile.TemporaryDirectory() as d:
        wav = Path(d) / "walk.wav"
        wav.write_bytes(b"x")

        ac = FakeAcoustic()
        dets = detector.detect(
            wav, lat=30.33, lon=76.40, week=41, min_conf=0.5, models=(ac, FakeGeo())
        )
        # min_conf 0.5 drops the 0.45 Magpie-Robin
        assert [x.common_name for x in dets] == [
            "Coppersmith Barbet",
            "Coppersmith Barbet",
            "Common Myna",
        ], dets
        # geo filter was passed through to BirdNET
        assert "custom_species_list" in ac.kwargs

        summary = detector.summarise(dets)
        assert summary[0]["common_name"] == "Coppersmith Barbet"
        assert summary[0]["count"] == 2
        assert abs(summary[0]["best_confidence"] - 0.91) < 1e-6

        # No Ollama running in tests -> graceful fallback, no crash
        text, used_llm = journal.write_entry(
            summary, "Test Park", "today", model="nonexistent", timeout=2
        )
        assert isinstance(text, str) and "Coppersmith Barbet" in text
        print("used_llm:", used_llm)
        print(text)

        # Empty detections
        text, used = journal.write_entry([], "Test Park", "today")
        assert "no confident" in text and not used

    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
