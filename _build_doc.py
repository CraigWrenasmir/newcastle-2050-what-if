"""
Build a single 'Newcastle 2050 — Raw Data Compendium.docx' from:
  - Event context (cover)
  - All audio transcripts (Night Culture x5, Transport x2)
  - All post-it transcriptions (3 batches, 297 notes)
  - Pointer to the live insights page

Workflow: assemble Markdown → pandoc → .docx
"""
import subprocess, pathlib, importlib.util, html as _html

ROOT = pathlib.Path(".")
TRANSCRIPTS = ROOT / "Transcripts"
OUT_MD  = ROOT / "_compendium.md"
OUT_DOCX = ROOT / "Newcastle 2050 — Raw Data Compendium.docx"

# Pull post-it data from the same source the HTML uses
spec = importlib.util.spec_from_file_location("data", "_postits_data.py")
data = importlib.util.module_from_spec(spec); spec.loader.exec_module(data)
items = data.POSTITS

CATS = [("transport", "🚲 Transport & Mobility"),
        ("health",    "🌿 Health & Wellbeing"),
        ("night",     "🪩 Night Culture & Economy")]

def md_clean(text):
    """Strip HTML entities and tags from post-it text for Markdown rendering."""
    return (text
            .replace("&amp;", "&")
            .replace("&quot;", '"')
            .replace("<em>", "_").replace("</em>", "_")
            .replace("<strong>", "**").replace("</strong>", "**"))

# ---- COVER ----
md = []
md += [
    "# Newcastle 2050: What If?",
    "## TEDxNewy Salon 1 — Raw Data Compendium",
    "",
    "**Date recorded:** 30 April – 1 May 2026",
    "**Compiled:** 3 May 2026",
    "",
    "---",
    "",
    "## About this document",
    "",
    "This is the raw, primary-source record of the data captured at TEDxNewy Salon 1, the *Newcastle 2050: What If?* community conversation. It contains:",
    "",
    "- **7 audio recordings** — verbatim transcriptions, ~104 minutes, ~15,000 words across two topics (Transport & Mobility, Night Culture & Economy)",
    "- **297 post-it notes** — transcribed from photographed table notes across three batches, deduplicated, organised by topic and sub-theme",
    "",
    "The companion analysis page — `insights.html`, in the same folder — is the **interactive layer**: themes, visualisations, sentiment matrices, pull-quotes, demographic gap chart, places-named chart, etc. Treat that page as the lens; treat this document as the source.",
    "",
    "## Three topics",
    "",
    "1. 🚲 **Transport & Mobility** — *How will we move through, in and out of Newcastle in 2050?*",
    "2. 🌿 **Health & Wellbeing** — *How will we live well in the city in 2050?*",
    "3. 🪩 **Night Culture & Economy** — *How will we experience the city after dark in 2050?*",
    "",
    "## Methodology",
    "",
    "- **Audio**: transcribed locally with whisper.cpp (`large-v3-turbo` model, English). No diarisation or speaker labels. Whisper occasionally loops on quiet audio — most notable in *Transport ZOOM0006*, which has a long \"I don't want to be pessimistic\" loop that is a transcription artefact, not real speech. Themes drawn from the substantive content only.",
    "- **Post-its**: read from photographs. Many post-its appear in multiple photographs (the table was re-shot from different angles); duplicates consolidated to one entry each, the most complete reading kept. Notes flagged `[reading uncertain]` are best-effort interpretations of unclear handwriting.",
    "- **Categorisation**: by *content*, not by paper colour (which didn't map cleanly).",
    "- **No audio for Health & Wellbeing** was recorded — that topic is sourced entirely from post-its.",
    "",
    "---",
    "",
    "# Part 1 — Audio transcripts",
    "",
    "Seven recordings, transcribed verbatim. No speaker labels.",
    "",
]

# ---- AUDIO TRANSCRIPTS ----
audio_files = [
    ("🚲 Transport & Mobility — Session 1 (ZOOM0005)", "Transport_ZOOM0005.txt", "~18 min · 3,415 words"),
    ("🚲 Transport & Mobility — Session 2 (ZOOM0006)", "Transport_ZOOM0006.txt", "~9 min · 1,145 words · contains transcription loop artefact"),
    ("🪩 Night Culture & Economy — Session 1 (ZOOM0001)", "NightCulture_ZOOM0001.txt", "~9 min · 1,566 words"),
    ("🪩 Night Culture & Economy — Session 2 (ZOOM0002)", "NightCulture_ZOOM0002.txt", "~2 min · 266 words"),
    ("🪩 Night Culture & Economy — Session 3 (ZOOM0003)", "NightCulture_ZOOM0003.txt", "~17 min · 2,262 words"),
    ("🪩 Night Culture & Economy — Session 4 (ZOOM0004)", "NightCulture_ZOOM0004.txt", "~3 min · 321 words"),
    ("🪩 Night Culture & Economy — Session 5 (ZOOM0005)", "NightCulture_ZOOM0005.txt", "~29 min · 6,101 words"),
]
for title, fname, meta in audio_files:
    p = TRANSCRIPTS / fname
    if not p.exists():
        continue
    md += ["", f"## {title}", "", f"*{meta}*", "", "```", p.read_text().strip(), "```", ""]

md += ["", "---", "", "# Part 2 — Post-it notes", "",
       f"**{len(items)} unique notes** across three batches, deduplicated and grouped by topic and sub-theme.",
       "",
       "Source image filenames (`IMG_4xxx`) and batch numbers (`b1` / `b2` / `b3`) are recorded against each note so you can trace any line back to the photograph.",
       ""]

# ---- POST-ITS ----
for cat, label in CATS:
    rows = [r for r in items if r[0] == cat]
    md += [f"## {label}", "", f"*{len(rows)} notes*", ""]
    seen, subs = set(), []
    for r in rows:
        if r[1] not in seen:
            seen.add(r[1]); subs.append(r[1])
    for sub in subs:
        sub_rows = [r for r in rows if r[1] == sub]
        md += [f"### {sub} ({len(sub_rows)})", ""]
        for _, _, text, src, batch in sub_rows:
            md.append(f"- {md_clean(text)}  ")
            md.append(f"  *{src} · batch {batch}*")
        md.append("")

# ---- CLOSING ----
md += [
    "---",
    "",
    "# Where to find more",
    "",
    "**Live, interactive analysis:** open `insights.html` (in this folder) in any browser.",
    "",
    "It contains:",
    "",
    "- Theme cards for each topic (synthesised from audio + post-its)",
    "- Visualisations: mode-of-transport mention frequency, the U-shaped service gap (night-time demographic chart), most-named places & venues (combined audio + post-its), sentiment matrices",
    "- Voice / pull-quote panels per topic",
    "- Sortable, sub-themed post-it grids",
    "- Embedded raw audio transcripts (no internet required)",
    "",
    "Every theme and quote on that page is favourite-able — click the heart and your favourites persist in your browser.",
    "",
    "---",
    "",
    "*End of compendium.*",
]

OUT_MD.write_text("\n".join(md))
print(f"Wrote {OUT_MD} ({OUT_MD.stat().st_size:,} bytes)")

# ---- CONVERT TO DOCX ----
result = subprocess.run([
    "pandoc",
    str(OUT_MD),
    "-o", str(OUT_DOCX),
    "--from", "markdown",
    "--to", "docx",
    "--toc",
    "--toc-depth=3",
    "--standalone",
], capture_output=True, text=True)
if result.returncode != 0:
    print("pandoc error:", result.stderr)
    raise SystemExit(1)

# Patch settings.xml so Word recomputes TOC page numbers on open.
# Without this, every TOC entry shows page "1" until the user manually updates fields.
import zipfile, shutil, tempfile, os, re as _re
tmpdir = pathlib.Path(tempfile.mkdtemp())
with zipfile.ZipFile(OUT_DOCX, "r") as z:
    z.extractall(tmpdir)

settings = tmpdir / "word" / "settings.xml"
xml = settings.read_text(encoding="utf-8")
if "<w:updateFields" not in xml:
    # Insert <w:updateFields w:val="true"/> as the first child of w:settings
    xml = _re.sub(
        r'(<w:settings\b[^>]*>)',
        r'\1<w:updateFields w:val="true"/>',
        xml,
        count=1,
    )
    settings.write_text(xml, encoding="utf-8")

# Re-zip into a fresh .docx
patched = OUT_DOCX.with_suffix(".patched.docx")
with zipfile.ZipFile(patched, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(tmpdir):
        for name in files:
            full = pathlib.Path(root) / name
            arc = full.relative_to(tmpdir)
            z.write(full, str(arc))
shutil.move(patched, OUT_DOCX)
shutil.rmtree(tmpdir)

print(f"Wrote {OUT_DOCX} ({OUT_DOCX.stat().st_size:,} bytes) — TOC will refresh on open")
