"""
Generate dot_editor.html — a local-only page for clicking dots to remove.

Embeds the current dots.json contents inline (so the editor works via file://
without CORS issues). After editing, the user downloads a cleaned dots.json
and runs _build_heatmap.py to regenerate the PNG.
"""
import json, pathlib, base64

dots = json.loads(pathlib.Path("dots.json").read_text())
img_b64 = base64.b64encode(pathlib.Path("Night Culture.png").read_bytes()).decode()

HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Dot editor — Night Culture map</title>
<style>
  :root {{ --bg:#1a1a1a; --ink:#fff; --muted:#aaa; --tedx:#eb0028; --kept:#ffea60; --gone:#666; }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: -apple-system, system-ui, sans-serif; }}
  header {{ padding: 14px 20px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
           background: #2a2a2a; border-bottom: 1px solid #333; position: sticky; top: 0; z-index: 10; }}
  header h1 {{ font-size: 16px; font-weight: 700; margin: 0; }}
  .status {{ font-size: 14px; color: var(--muted); }}
  .status strong {{ color: var(--ink); font-variant-numeric: tabular-nums; }}
  .spacer {{ flex: 1; }}
  button {{ background: var(--tedx); color: white; border: 0; padding: 9px 14px; border-radius: 6px;
            cursor: pointer; font-size: 13px; font-weight: 600; }}
  button:hover {{ filter: brightness(1.1); }}
  button.ghost {{ background: transparent; color: var(--ink); border: 1px solid #444; }}
  .hint {{ padding: 12px 20px; background: #222; color: var(--muted); font-size: 13px; }}
  .hint kbd {{ background: #333; padding: 2px 6px; border-radius: 3px; font-size: 12px; }}
  .stage {{ padding: 20px; }}
  .map-wrap {{ position: relative; max-width: 100%; margin: 0 auto; }}
  .map-wrap img {{ width: 100%; height: auto; display: block; border-radius: 8px; }}
  .map-wrap svg {{ position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }}
  .map-wrap svg circle {{ pointer-events: all; cursor: pointer; transition: all .12s ease; }}
  .map-wrap svg circle.kept {{ fill: var(--kept); fill-opacity: .85; stroke: white; stroke-width: 1.5; filter: drop-shadow(0 0 6px rgba(255,234,96,.7)); }}
  .map-wrap svg circle.gone {{ fill: none; stroke: var(--gone); stroke-width: 1.5; stroke-dasharray: 3,3; }}
  .map-wrap svg circle:hover {{ stroke-width: 3; transform-origin: center; }}
</style>
</head>
<body>

<header>
  <h1>🟡 Dot editor — Night Culture map</h1>
  <span class="status"><strong id="kept">0</strong> kept, <strong id="gone">0</strong> removed (of <strong id="total">0</strong>)</span>
  <span class="spacer"></span>
  <button id="reset" class="ghost">Reset</button>
  <button id="save">Download cleaned dots.json</button>
</header>

<div class="hint">
  Click a yellow dot to mark it for removal (it'll go grey-dashed). Click again to bring it back. When you're done, hit <strong>Download cleaned dots.json</strong>, drop the new file into the TEDx Data folder replacing the existing one, then run <kbd>python3 _build_heatmap.py</kbd> to regenerate the heat map.
</div>

<div class="stage">
  <div class="map-wrap" id="wrap">
    <img id="map" src="data:image/png;base64,{img_b64}" alt="Night Culture map">
    <svg id="overlay" viewBox="0 0 100 100" preserveAspectRatio="none"></svg>
  </div>
</div>

<script>
const DOTS = {json.dumps(dots, indent=2)};
const overlay = document.getElementById('overlay');
const keptEl = document.getElementById('kept');
const goneEl = document.getElementById('gone');
const totalEl = document.getElementById('total');

// SVG viewBox in 0-100 coords matched to image; we'll use percentage coords
const W = DOTS.clean_dim[0], H = DOTS.clean_dim[1];
overlay.setAttribute('viewBox', `0 0 ${{W}} ${{H}}`);

const states = DOTS.dots.map(() => 'kept');

function render() {{
  overlay.innerHTML = '';
  let kept = 0, gone = 0;
  DOTS.dots.forEach((d, i) => {{
    const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    c.setAttribute('cx', d.x * W);
    c.setAttribute('cy', d.y * H);
    c.setAttribute('r', 28);
    c.setAttribute('class', states[i]);
    c.dataset.idx = i;
    c.addEventListener('click', () => {{
      states[i] = states[i] === 'kept' ? 'gone' : 'kept';
      c.setAttribute('class', states[i]);
      updateCounts();
    }});
    overlay.appendChild(c);
    if (states[i] === 'kept') kept++; else gone++;
  }});
  totalEl.textContent = DOTS.dots.length;
  keptEl.textContent = kept;
  goneEl.textContent = gone;
}}

function updateCounts() {{
  let kept = 0, gone = 0;
  states.forEach(s => s === 'kept' ? kept++ : gone++);
  keptEl.textContent = kept;
  goneEl.textContent = gone;
}}

document.getElementById('reset').addEventListener('click', () => {{
  states.fill('kept');
  render();
}});

document.getElementById('save').addEventListener('click', () => {{
  const cleaned = {{
    count: states.filter(s => s === 'kept').length,
    photo_dim: DOTS.photo_dim,
    clean_dim: DOTS.clean_dim,
    dots: DOTS.dots.filter((_, i) => states[i] === 'kept'),
  }};
  const blob = new Blob([JSON.stringify(cleaned, null, 2)], {{ type: 'application/json' }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'dots.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}});

render();
</script>

</body>
</html>
"""

pathlib.Path("dot_editor.html").write_text(HTML)
print(f"Wrote dot_editor.html with {dots['count']} dots embedded")
