# Newcastle 2050: What If?

Citizen conversations on the future of the city, captured at **TEDxNewy Salon 1** — 30 April – 1 May 2026.

## Live page

**[Open the interactive insights page →](https://craigwrenasmir.github.io/newcastle-2050-what-if/)**

Three topic areas, plus a synthesis layer:

- 🚲 **Transport & Mobility** — *How will we move through, in and out of Newcastle in 2050?*
- 🌿 **Health & Wellbeing** — *How will we live well in the city in 2050?*
- 🪩 **Night Culture & Economy** — *How will we experience the city after dark in 2050?*
- 🔗 **Threads across the conversation** — cross-cutting themes and tension pairs

## What's in this repo

| File / folder | What it is |
|---|---|
| `insights.html` | The interactive analysis page (themes, visualisations, voice quotes, post-it grids, raw transcripts). Open in any browser. |
| `Newcastle 2050 — Raw Data Compendium.docx` | Print-ready Word document with all raw data (audio transcripts + 297 post-its). |
| `Transcripts/` | Plain-text transcripts of all 7 audio recordings, plus the post-it transcription source (`PostIts_Raw.md`). |
| `_postits_data.py` | The single source-of-truth for all 297 post-it notes (category, sub-theme, text, source image, batch). |
| `_build_postits.py` | Regenerates the post-it grids in `insights.html` and the post-it markdown from `_postits_data.py`. |
| `_build_doc.py` | Builds the Word compendium from the audio transcripts and post-it data. |
| `_compendium.md` | Combined raw-data markdown (the source for the Word doc). |

## Data summary

- **7 audio recordings** — ~104 minutes, ~15,000 words, transcribed locally with [whisper.cpp](https://github.com/ggerganov/whisper.cpp) (`large-v3-turbo`).
- **297 unique post-it notes** — transcribed from 83 photographs across three batches; deduplicated; categorised by content.
- No audio was recorded for the Health & Wellbeing table — that topic is sourced entirely from post-its.

## Methodology notes

- Whisper occasionally loops on quiet stretches of audio. Most notably *Transport ZOOM0006* contains a long "I don't want to be pessimistic" repeat that's a transcription artefact, not real speech. Themes are based on substantive content only.
- Post-its were re-photographed from multiple angles per table — duplicates have been consolidated to one entry each, with the most complete reading retained.
- Reading uncertainty is flagged in the data with `[reading uncertain]`.
- Categorisation is by content, not by paper colour (which didn't map cleanly to topics).

## Updating

To update the page or document after adding more post-it data:

```bash
# 1. Edit _postits_data.py (append new entries)
# 2. Regenerate the page + raw markdown:
python3 _build_postits.py
# 3. Rebuild the Word document:
python3 _build_doc.py
```
