# birdjournal - offline bird call field journal

Record birds on a walk, then get a species list and a short field-journal
entry. Everything runs on your own machine. No cloud, no API keys, no account.

**Open pieces doing the real work**
- **BirdNET** (open-source bird sound classifier) identifies species from audio
- **An open-weight LLM via Ollama** (Qwen, Gemma, Llama - your pick) writes the journal
- Both run locally, so it works on the trail with no signal

## Setup (one time, needs internet)

```bash
pip install -r requirements.txt

# Install Ollama from https://ollama.com, then:
ollama pull qwen2.5:3b        # small, fast, fine on a laptop

# First run downloads BirdNET weights (~50 MB) and caches them.
# After that, everything works offline.
```

## Use

1. Record birds with your phone's voice recorder (get close, 2-10 minutes, early morning is best).
2. Copy the file to your laptop.
3. Run:

```bash
python main.py walk.wav --place "Sheesh Mahal Gardens, Patiala" \
    --lat 30.33 --lon 76.40 --out journal.md
```

Useful options:
- `--lat/--lon` makes BirdNET ignore species that don't live near you (fewer false positives)
- `--model gemma3:4b` swaps the LLM; swapping models is one flag
- `--language Hindi` (or Punjabi) writes the journal in that language
- `--min-conf 0.5` is stricter, `0.3` is more generous

No Ollama running? It still prints the species list and a plain summary.

## Run the self-test

```bash
python test_pipeline.py
```

This uses a fake BirdNET to check the parsing, summary and fallback logic.

## Outdoor test plan (for the "bonus points" part)

1. Pick one spot (park, canal bank, university garden). Go at sunrise.
2. Record 10 minutes. **Put the phone away.** Just listen and look.
3. Write down, by eye, every bird you can name yourself.
4. Run birdjournal later. Compare: what did it catch that you missed? What did it get wrong?
5. Report honestly in your post: matches, misses, false positives.

## Notes for your post (why open matters here)

- **Works with no signal.** Models are cached locally; the trail needs no internet.
- **Your recordings stay on your machine.** No audio uploaded anywhere.
- **Swap or tune freely.** Change the LLM with one flag; BirdNET also supports custom species lists and training on your own recordings.
- **Costs nothing to run.** No per-call API fees.

## Troubleshooting

- `requires TensorFlow` error: this project passes `library="litert"` so it isn't needed. Make sure `birdnet>=1.1` is installed.
- Model download fails: the first run needs access to zenodo.org. Run it once on a normal connection.
- Journal says "Local LLM not running": start Ollama (`ollama serve`) and check `ollama list` shows your model.
- Nothing detected: record closer, avoid wind noise, lower `--min-conf`.

## Honest limitations

- BirdNET is stronger on Europe/North America than South Asia; expect some misses and some wrong guesses. That is worth reporting in your post.
- The LLM only rewrites BirdNET's output. Check species against what you actually saw.
