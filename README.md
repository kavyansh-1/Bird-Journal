# 🐦 birdjournal

**An offline bird-call field journal.** Record birds on a walk, put the phone away, and let open-source AI tell you who was singing, with no internet, no account and no cloud.

Built for the [Hacktoberfest Open-Source AI Challenge, Week 1: Touch Grass](https://dev.to/challenges/hacktoberfest-week1-2026-10-05).

```
$ python main.py barbet.wav --place "Sikar, Rajasthan" --lat 27.6 --lon 75.14 --out test.md

Species heard: 1
  Coppersmith Barbet           x16  best 100%  first at 0s
```

## How it works

```
 phone recording (.wav/.mp3)
          |
          v
   BirdNET (open source)  ---- geo filter (lat/lon) removes species that don't live nearby
          |
          v
   species list + confidence
          |
          v
   local LLM via Ollama (open weights)
          |
          v
   short field-journal entry (English / Hindi / Punjabi ...)
```

The idea is that the screen is the shortest part of the experience. You go outside, record, and listen. The tool does its work afterwards.

## Open-source pieces

| Piece | Role |
|---|---|
| [BirdNET](https://github.com/birdnet-team/BirdNET-Analyzer) | Identifies species from sound. Runs through the `litert` backend, so TensorFlow is not required. |
| [Ollama](https://ollama.com) + an open-weight LLM (default `qwen2.5:3b`) | Writes the journal entry on your machine. Swap the model with `--model`. |

## Why open matters here

- **Works with no signal.** The models (about 77 MB and 46 MB) download once and are cached. After that, the trail needs no internet.
- **Your recordings stay on your machine.** No audio is uploaded anywhere.
- **Free to run.** No API keys and no per-call fees.
- **Swappable and fixable.** Change the language model with one flag, or change the prompt when it misbehaves.

## Setup

You need Python 3.10+ and internet for the first run only.

```bash
git clone <your-repo-url>
cd birdjournal
pip install -r requirements.txt

# Install Ollama from https://ollama.com, then pull a small model:
ollama pull qwen2.5:3b
```

The first run downloads BirdNET's model weights and caches them. After that, everything works offline.

## Usage

1. Record birds with your phone's voice recorder. Get close, record 2 to 10 minutes, and early morning is best.
2. Copy the file to your computer.
3. Run:

```bash
python main.py walk.wav --place "Your park or garden" --lat 30.33 --lon 76.40 --out journal.md
```

### Options

| Flag | What it does |
|---|---|
| `--place` | Place name used in the journal |
| `--lat`, `--lon` | Location. Turns on BirdNET's location filter, which cuts false positives |
| `--min-conf` | Minimum confidence, default `0.4`. Higher is stricter |
| `--model` | Any Ollama model, e.g. `gemma3:4b` |
| `--language` | Journal language, e.g. `Hindi` or `Punjabi` |
| `--out` | Save the entry and species table to a Markdown file |

If Ollama is not running, the tool still prints the species list and a plain-text summary.

## Project layout

```
main.py            command-line entry point
detector.py        runs BirdNET and groups detections by species
journal.py         prompts the local LLM and writes the journal entry
test_pipeline.py   offline smoke test using a fake BirdNET
requirements.txt
```

## Tests

```bash
python test_pipeline.py
```

This uses a fake BirdNET, so it needs no model download. It checks result parsing, confidence filtering, the location-filter hand-off, the species summary and the no-Ollama fallback.

## Results so far

Tested on a 46-second recording of a Coppersmith Barbet from Sikar, Rajasthan, taken from [Xeno-canto](https://xeno-canto.org) (recordist: Dipendra Maharshi, [add license]). BirdNET identified it at 100% confidence in all 16 of its 3-second windows.

That was a loud, clean clip, so it checks that the pipeline works, not how accurate it is on real field audio. **Field-walk results:** [add yours here].

## What I learned

- My first journal prompt let the small model invent facts that were not in the detections, such as calling the barbet "colorful and melodious". It also reported "heard 16 times" when it meant 16 three-second windows. The prompt now asks for three first-person sentences using only the listed facts, and reports "detected in N windows".
- Small local models need guardrails like this. The model is only rewriting BirdNET's output, so it should not add anything of its own.

## Limitations

- BirdNET is trained on more data from Europe and North America than South Asia, so expect misses and wrong guesses.
- The "count" is the number of 3-second windows with a detection, not the number of individual calls.
- The journal is generated text. Check the species against what you saw.

## Troubleshooting

- **`requires TensorFlow` error:** the project passes `library="litert"`, so TensorFlow is not needed. Make sure `birdnet>=1.1` is installed.
- **Model download fails:** the first run needs access to zenodo.org. Run it once on a normal connection.
- **"Local LLM not running":** start Ollama (`ollama serve`) and check that `ollama list` shows your model.
- **Nothing detected:** record closer, avoid wind noise, or lower `--min-conf`.

## Credits

- [BirdNET](https://github.com/birdnet-team/BirdNET-Analyzer) by the K. Lisa Yang Center for Conservation Bioacoustics at the Cornell Lab of Ornithology and Chemnitz University of Technology.
- Test recording from [Xeno-canto](https://xeno-canto.org), recorded by Dipendra Maharshi.
- [Ollama](https://ollama.com) and the open-weight model authors.

## License

[Choose a license, e.g. MIT, and add a LICENSE file.]
