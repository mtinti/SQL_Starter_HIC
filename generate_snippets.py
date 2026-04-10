from pathlib import Path
import re
import html as html_mod

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
.code-panel{display:none;overflow:auto}
.code-panel.active{display:block}
pre{margin:0;padding:0.85rem 0;line-height:1.5;font-size:12px;white-space:pre;min-width:max-content}
.line{display:flex;align-items:flex-start}
.line-no{position:sticky;left:0;flex:0 0 auto;width:2.5em;padding:0 0.8em 0 0.9rem;text-align:right;color:#6c7086;border-right:1px solid #313244;user-select:none;background:var(--surface);z-index:1}
.line-content{flex:0 0 auto;padding:0 0.9rem 0 0.8em;white-space:pre}
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
async function copyActive(btn) {
  var block = btn.closest('.snippet');
  var activePanel = block.querySelector('.code-panel.active');
  var text = '';
  if (activePanel) {
    var contents = activePanel.querySelectorAll('.line-content');
    if (contents.length) {
      text = Array.prototype.map.call(contents, function (n) { return n.innerText; }).join('\\n');
    } else {
      var pre = activePanel.querySelector('pre');
      text = pre ? pre.innerText : '';
    }
  }
  try {
    await navigator.clipboard.writeText(text);
    var old = btn.textContent;
    btn.textContent = 'Copied';
    setTimeout(function () { btn.textContent = old; }, 1200);
  } catch (e) {
    btn.textContent = 'Copy failed';
    setTimeout(function () { btn.textContent = 'Copy'; }, 1200);
  }
}
</script>'''


TAG_RE = re.compile(r'<(/?)(\w+)([^>]*)>')


def split_pre_lines(inner_html):
    """Split a <pre> inner HTML into lines while preserving highlight spans.

    Any opening tag that is still active when we hit a newline is closed at
    end-of-line and reopened on the next line, so every line is a well-formed
    HTML fragment even if the original markup contained multi-line spans
    (e.g. a string literal spanning several lines).
    """
    # Trim a single trailing newline if present so we don't get a phantom line.
    if inner_html.endswith('\n'):
        inner_html = inner_html[:-1]

    lines = [[]]
    open_stack = []  # list of (full_open_tag, tag_name)
    i = 0
    n = len(inner_html)
    while i < n:
        ch = inner_html[i]
        if ch == '<':
            end = inner_html.find('>', i)
            if end == -1:
                raise ValueError('Unclosed tag in pre content')
            tag = inner_html[i:end + 1]
            m = TAG_RE.match(tag)
            if m is None:
                # Not a recognisable tag, treat as literal text.
                lines[-1].append(tag)
            else:
                is_close = bool(m.group(1))
                name = m.group(2)
                self_close = tag.endswith('/>')
                if is_close:
                    if open_stack and open_stack[-1][1] == name:
                        open_stack.pop()
                    lines[-1].append(tag)
                elif self_close:
                    lines[-1].append(tag)
                else:
                    open_stack.append((tag, name))
                    lines[-1].append(tag)
            i = end + 1
        elif ch == '\n':
            # Close any still-open tags at end of current line.
            for _tag, name in reversed(open_stack):
                lines[-1].append('</{0}>'.format(name))
            # Start a new line and re-open the same tags.
            new_line = [tag for tag, _name in open_stack]
            lines.append(new_line)
            i += 1
        else:
            lines[-1].append(ch)
            i += 1

    return [''.join(parts) for parts in lines]


def number_pre_blocks(block_html):
    """Wrap every line of every <pre> in the block with line-number markup."""
    out = []
    cursor = 0
    while True:
        start = block_html.find('<pre', cursor)
        if start == -1:
            out.append(block_html[cursor:])
            break
        open_end = block_html.find('>', start)
        if open_end == -1:
            raise ValueError('Unclosed <pre> opening tag')
        close = block_html.find('</pre>', open_end)
        if close == -1:
            raise ValueError('Missing </pre>')
        out.append(block_html[cursor:open_end + 1])
        inner = block_html[open_end + 1:close]
        lines = split_pre_lines(inner)
        rendered = []
        for idx_line, line in enumerate(lines, start=1):
            content = line if line else ' '
            rendered.append(
                '<span class="line">'
                '<span class="line-no">{0}</span>'
                '<span class="line-content">{1}</span>'
                '</span>'.format(idx_line, content)
            )
        out.append(''.join(rendered))
        out.append('</pre>')
        cursor = close + len('</pre>')
    return ''.join(out)


for n, block in enumerate(blocks):
    block = block.replace('class="code-block"', 'class="snippet"', 1)
    tabs_end = block.find('</div>', block.find('<div class="code-tabs">'))
    if tabs_end != -1:
        block = (
            block[:tabs_end]
            + '<button class="copy-btn" onclick="copyActive(this)">Copy</button>'
            + block[tabs_end:]
        )
    block = number_pre_blocks(block)
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
