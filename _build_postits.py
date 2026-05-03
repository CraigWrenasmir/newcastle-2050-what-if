"""
Regenerate post-it sections in insights.html and PostIts_Raw.md from _postits_data.py.
"""
import re, html, pathlib, importlib.util

spec = importlib.util.spec_from_file_location("data", "_postits_data.py")
data = importlib.util.module_from_spec(spec); spec.loader.exec_module(data)
items = data.POSTITS

CATS = [("transport","🚲 Transport &amp; Mobility"),
        ("health","🌿 Health &amp; Wellbeing"),
        ("night","🪩 Night Culture &amp; Economy")]

# ---------- HTML generation helpers ----------
def render_grid(cat):
    rows = [r for r in items if r[0] == cat]
    # group by sub, preserving first-appearance order
    seen, subs = set(), []
    for r in rows:
        if r[1] not in seen:
            seen.add(r[1]); subs.append(r[1])
    out = []
    for sub in subs:
        sub_rows = [r for r in rows if r[1] == sub]
        out.append(f'<div class="postit-subgroup">')
        out.append(f'  <h4 class="postit-subhead">{sub}<span class="count">{len(sub_rows)}</span></h4>')
        out.append(f'  <div class="postit-grid">')
        for i, (_, _, text, src, batch) in enumerate(sub_rows):
            pid = f"p-{cat}-{sub.lower().replace(' ','-').replace('&','').replace(',','').replace(';','')}-{i}"
            out.append(
                f'    <div class="postit" data-id="{pid}">'
                f'<button class="fav" aria-label="favourite">♥</button>{text}'
                f'<span class="src">{src} · b{batch}</span></div>'
            )
        out.append('  </div>')
        out.append('</div>')
    return "\n".join(out), len(rows)

def update_section(src, cat, count_label):
    """Replace the entire post-it block for a given category."""
    # Pattern: from "<h2 class="section-title">Paper notes &amp; post-its..." to closing </div> of the grid
    # We marked grids by either:
    #   <div class="postit-grid">...</div>
    # We'll match the heading + grid greedily up to next </div> sibling closure.
    cat_anchor = {
        "transport": '<!-- ============================================================\n     HEALTH',
        "health": '<h2 class="section-title">Audio recordings</h2>',
        "night": '</section>\n\n\n<footer class="foot">',
    }
    # Find the heading
    heading_re = re.compile(
        r'<h2 class="section-title">Paper notes &amp; post-its.*?</h2>\s*<div class="postit-grid">.*?</div>\s*\n',
        re.DOTALL
    )
    # We need per-category replacement. The simplest robust way: match the heading_block_then_grid
    # Use a positional approach - first occurrence in transport section, second in health, third in night.
    matches = list(heading_re.finditer(src))
    return matches

# Read insights
html_path = pathlib.Path("insights.html")
html_src = html_path.read_text()

# Find the three post-it blocks (heading + first grid div)
# Strategy: three consecutive blocks matching the pattern - replace each with the rendered grid for the appropriate cat
# Match heading + ALL content until next <h2> or </section>
pattern = re.compile(
    r'<h2 class="section-title">Paper notes &amp; post-its.*?(?=<h2 class="section-title"|</section>)',
    re.DOTALL
)
matches = list(pattern.finditer(html_src))
print(f"Found {len(matches)} post-it sections")

if len(matches) != 3:
    print("WARN: expected 3 post-it sections — got", len(matches))

# Replace from the back so offsets stay valid
# Match order in document is: transport, health, night
order = ["transport", "health", "night"]
new_src = html_src
for cat, m in reversed(list(zip(order, matches))):
    grid_html, n = render_grid(cat)
    label = {"transport":"Transport &amp; Mobility",
             "health":"Health &amp; Wellbeing",
             "night":"Night Culture &amp; Economy"}[cat]
    # Determine batch label dynamically from data
    batches = sorted({r[4] for r in items if r[0] == cat})
    if len(batches) == 1:
        blabel = f"batch {batches[0]}"
    else:
        blabel = f"batches {batches[0]}–{batches[-1]} (final)"
    new_block = (
        f'<h2 class="section-title">Paper notes &amp; post-its '
        f'<span style="font-family:-apple-system,system-ui,sans-serif;font-size:13px;'
        f'color:var(--muted);font-weight:400;margin-left:8px">'
        f'{n} notes across {blabel}</span></h2>\n'
        f'{grid_html}\n'
    )
    new_src = new_src[:m.start()] + new_block + new_src[m.end():]

# Update header count to reflect total (only the masthead .meta one, not category heroes)
total = len(items)
new_src = re.sub(
    r'(<div class="meta">.*?<div><strong>)\d+(</strong>post-it notes</div>)',
    rf'\g<1>{total}\g<2>',
    new_src,
    flags=re.DOTALL
)

# Update per-category hero post-it counts (idempotent)
nt = sum(1 for r in items if r[0] == "transport")
nh = sum(1 for r in items if r[0] == "health")
nn = sum(1 for r in items if r[0] == "night")

new_src = re.sub(
    r'(How will we move through, in and out of Newcastle in 2050\?.*?<div><strong>~4,500</strong>words</div>)<div><strong>\d+</strong>post-it notes</div>',
    rf'\g<1><div><strong>{nt}</strong>post-it notes</div>',
    new_src, flags=re.DOTALL
)
new_src = re.sub(
    r'(How will we live well in the city in 2050\?.*?<div class="stats">\s*)<div><strong>\d+</strong>post-it notes</div>',
    rf'\g<1><div><strong>{nh}</strong>post-it notes</div>',
    new_src, flags=re.DOTALL
)
new_src = re.sub(
    r'(How will we experience the city after dark in 2050\?.*?<div><strong>~10,500</strong>words</div>)<div><strong>\d+</strong>post-it notes</div>',
    rf'\g<1><div><strong>{nn}</strong>post-it notes</div>',
    new_src, flags=re.DOTALL
)

html_path.write_text(new_src)
print(f"Updated insights.html: {nt} transport, {nh} health, {nn} night = {total} total post-its")

# ---------- Build raw transcript markdown ----------
def render_md():
    lines = ["# Post-it transcriptions — TEDxNewy Salon 1",
             "",
             f"Total notes (batches 1 & 2 combined, deduplicated): **{total}**",
             "",
             "Source: HEIC photos in `Post Its/` (batch 1 archived in `Post Its/Archive/`).",
             "Categorised by content. Where the same note appears in multiple photos (table re-photographed from different angles), only the most complete reading is kept.",
             "Batch label: **b1** = first photo set; **b2** = second photo set. `[?]` flags an uncertain reading.",
             ""]
    for cat, label in CATS:
        rows = [r for r in items if r[0] == cat]
        plain_label = label.replace("&amp;", "&")
        lines += [f"## {plain_label}", "", f"_{len(rows)} notes_", ""]
        # group by sub
        seen, subs = set(), []
        for r in rows:
            if r[1] not in seen:
                seen.add(r[1]); subs.append(r[1])
        for sub in subs:
            sub_rows = [r for r in rows if r[1] == sub]
            lines.append(f"### {sub} ({len(sub_rows)})")
            lines.append("")
            for _, _, text, src, batch in sub_rows:
                # Strip HTML entities for markdown
                t = text.replace("&amp;","&").replace("&quot;",'"')
                lines.append(f"- {t}  \n  _{src} · batch {batch}_")
            lines.append("")
    return "\n".join(lines)

pathlib.Path("Transcripts/PostIts_Raw.md").write_text(render_md())
print(f"Wrote Transcripts/PostIts_Raw.md ({total} entries)")
