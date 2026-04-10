from pathlib import Path
import re

source = Path('getting-started-draft.html').read_text(encoding='utf-8')

start_tag = '<div class="code-block">'
idx = 0
blocks = []
while True:
    start = source.find(start_tag, idx)
    if start == -1:
        break
    i = start
    depth = 0
    while i < len(source):
        next_open = source.find('<div', i)
        next_close = source.find('</div>', i)
        if next_close == -1:
            raise RuntimeError('Unmatched div')
        if next_open != -1 and next_open < next_close:
            depth += 1
            i = next_open + 4
        else:
            depth -= 1
            i = next_close + 6
            if depth == 0:
                blocks.append(source[start:i])
                idx = i
                break

out_dir = Path('.')

style = '''<style>
:root {
  --bg: #0f1220;
  --surface: #11152a;
  --border: #313244;
  --text: #cdd6f4;
  --muted: #94a3b8;
  --active: #cba6f7;
  --tab-bg: #181825;
  --btn-bg: #1f2937;
  --btn-hover: #334155;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,Liberation Mono,monospace;color:var(--text)}
.snippet{margin:0;border:1px solid var(--border);border-radius:8px;overflow:hidden;background:var(--surface)}
.code-tabs{display:flex;gap:2px;align-items:center;background:var(--tab-bg);border-bottom:1px solid var(--border);padding-right:0.5rem}
.code-tab{font-size:12px;padding:0.55rem 0.9rem;border:none;background:transparent;color:var(--muted);cursor:pointer}
.code-tab.active{color:var(--text);border-bottom:2px solid var(--active)}
.copy-btn{margin-left:auto;background:var(--btn-bg);color:var(--text);border:1px solid var(--border);font-size:12px;padding:0.3rem 0.55rem;border-radius:4px;cursor:pointer}
.copy-btn:hover{background:var(--btn-hover)}
.code-panel{display:none;padding:0.85rem 0.9rem;overflow:auto}
.code-panel.active{display:block}
pre{margin:0;line-height:1.5;font-size:12px;white-space:pre}
.line{display:grid;grid-template-columns:2.5em 1fr;column-gap:0.8em}
.line-no{color:#6c7086;text-align:right;border-right:1px solid #313244;padding-right:0.8em;user-select:none}
.line-content{white-space:pre}
.cm{color:#6c7086}.kw{color:#cba6f7}.fn{color:#89b4fa}.st{color:#a6e3a1}.nb{color:#fab387}
</style>'''

script = '''<script>
function switchTab(button, panelId) {
  const block = button.closest('.snippet');
  block.querySelectorAll('.code-tab').forEach(t => t.classList.remove('active'));
  button.classList.add('active');
  block.querySelectorAll('.code-panel').forEach(p => p.classList.remove('active'));
  block.querySelector('#' + panelId).classList.add('active');
}
function addLineNumbers() {
  document.querySelectorAll('pre').forEach(pre => {
    const html = pre.innerHTML.replace(/\n$/, '');
    const lines = html.split('\n');
    pre.innerHTML = lines.map((line, idx) => (
      `<span class="line"><span class="line-no">${idx + 1}</span><span class="line-content">${line || ' '}</span></span>`
    )).join('');
  });
}
async function copyActive(btn) {
  const block = btn.closest('.snippet');
  const activePre = block.querySelector('.code-panel.active pre');
  const text = activePre ? activePre.innerText : '';
  try {
    await navigator.clipboard.writeText(text);
    const old = btn.textContent;
    btn.textContent = 'Copied';
    setTimeout(() => btn.textContent = old, 1200);
  } catch (e) {
    btn.textContent = 'Copy failed';
    setTimeout(() => btn.textContent = 'Copy', 1200);
  }
}
document.addEventListener('DOMContentLoaded', addLineNumbers);
</script>'''

for n, block in enumerate(blocks):
    block = block.replace('class="code-block"', 'class="snippet"', 1)
    tabs_end = block.find('</div>', block.find('<div class="code-tabs">'))
    if tabs_end != -1:
      block = block[:tabs_end] + '<button class="copy-btn" onclick="copyActive(this)">Copy</button>' + block[tabs_end:]
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Snippet {n:03d}</title>
{style}
</head>
<body>
{block}
{script}
</body>
</html>
'''
    (out_dir / f'snippet_{n:03d}.html').write_text(html, encoding='utf-8')

print(f'Generated {len(blocks)} snippets')
