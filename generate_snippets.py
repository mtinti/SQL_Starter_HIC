from pathlib import Path

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
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,Liberation Mono,monospace;color:var(--text)}
.snippet{margin:0;border:1px solid var(--border);border-radius:8px;overflow:hidden;background:var(--surface)}
.code-tabs{display:flex;gap:2px;background:var(--tab-bg);border-bottom:1px solid var(--border)}
.code-tab{font-size:12px;padding:0.55rem 0.9rem;border:none;background:transparent;color:var(--muted);cursor:pointer}
.code-tab.active{color:var(--text);border-bottom:2px solid var(--active)}
.code-panel{display:none}
.code-panel.active{display:block}
pre{margin:0;padding:0.85rem 0.9rem;overflow:auto;line-height:1.5;font-size:12px;white-space:pre}
.cm{color:#6c7086}.kw{color:#cba6f7}.fn{color:#89b4fa}.st{color:#a6e3a1}.nb{color:#fab387}
</style>'''

script = '''<script>
function switchTab(button, panelId) {
  var block = button.closest('.snippet');
  block.querySelectorAll('.code-tab').forEach(function (t) { t.classList.remove('active'); });
  button.classList.add('active');
  block.querySelectorAll('.code-panel').forEach(function (p) { p.classList.remove('active'); });
  var panel = block.querySelector('#' + panelId);
  if (panel) panel.classList.add('active');
}
</script>'''

for n, block in enumerate(blocks):
    block = block.replace('class="code-block"', 'class="snippet"', 1)
    page = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Snippet {index:03d}</title>
{style}
</head>
<body>
{block}
{script}
</body>
</html>
'''.format(index=n, style=style, block=block, script=script)
    (out_dir / 'snippet_{0:03d}.html'.format(n)).write_text(page, encoding='utf-8')

print('Generated {0} snippets'.format(len(blocks)))
