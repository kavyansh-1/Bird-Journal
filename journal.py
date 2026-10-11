"""Turn bird detections into a short field-journal entry using a LOCAL LLM.

Talks to Ollama (https://ollama.com) on localhost, so nothing leaves your
machine. If Ollama isn't running, we fall back to a plain template so the
tool still works with zero setup.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"


def _prompt(summary: list[dict], place: str, when: str, language: str) -> str:
    lines = "\n".join(
        f"- {s['common_name']} ({s['scientific_name']}): detected in "
        f"{s['count']} three-second windows, best confidence "
        f"{s['best_confidence']:.0%}"
        for s in summary
    )
    return (
        "You write a short first-person field-journal entry for someone who "
        "just went birding.\n"
        f"Place: {place}\nTime: {when}\nLanguage: {language}\n\n"
        "A bird-sound detector (BirdNET) reported the species below. Rules:\n"
        "- Write exactly 3 sentences, in first person ('I heard...').\n"
        "- Use ONLY the facts listed. Do not add habitat, appearance, or "
        "behaviour facts that are not listed. Do not invent species.\n"
        "- Say 'detected in N windows', never 'heard N times'.\n"
        "- If confidence is under 60%, say it is uncertain.\n"
        "- Then add one final line starting with 'Try next time:' that "
        "suggests putting the phone away and looking for the bird by eye. "
        "Write that line only once.\n\n"
        f"Detections:\n{lines}\n"
    )


def _fallback(summary: list[dict], place: str, when: str) -> str:
    if not summary:
        return (
            f"{when} at {place}: no confident bird calls detected. "
            "Try a quieter spot, or record closer to dawn."
        )
    names = ", ".join(s["common_name"] for s in summary)
    return (
        f"{when} at {place}: heard {len(summary)} species - {names}. "
        "(Local LLM not running, so this is a plain summary. "
        "Start Ollama for a written journal entry.)"
    )


def write_entry(
    summary: list[dict],
    place: str = "somewhere outdoors",
    when: str = "this morning",
    model: str = "qwen2.5:3b",
    language: str = "English",
    timeout: int = 120,
) -> tuple[str, bool]:
    """Return (text, used_llm)."""
    if not summary:
        return _fallback(summary, place, when), False

    body = json.dumps(
        {
            "model": model,
            "prompt": _prompt(summary, place, when, language),
            "stream": False,
            "options": {"temperature": 0.4},
        }
    ).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.load(resp)
        text = data.get("response", "").strip()
        if text:
            return text, True
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        pass
    return _fallback(summary, place, when), False