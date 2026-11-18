"""Shared design system for the profile: one cerulean palette, two themes, small SVG helpers. Standard library only."""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'assets')
W = 846                                   # width GitHub gives a profile README on a wide screen

MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"

# cerulean #007BA7 is the one brand colour; everything else is a tint or a shade of it
THEMES = {
    'dark': dict(bg='#0d1117', panel='#0A1B24', panel2='#0E2632', line='#16485C', ink='#E4F6FC', soft='#93BCCB', mute='#557F90',
                 core='#007BA7', hi='#35B6E6', glow='#8ADBF7', deep='#0A5F82', night='#061219',
                 tones=['#0F5270', '#0F6184', '#0C7098', '#0880AD', '#0A93C4', '#22A7D8', '#45BAE5', '#73CDEF', '#A8E1F7', '#E6F8FE']),
    'light': dict(bg='#ffffff', panel='#F2FAFD', panel2='#E3F3F9', line='#B7DDEB', ink='#05354A', soft='#41707F', mute='#7BA3B2',
                  core='#007BA7', hi='#0A93C4', glow='#005B80', deep='#00506F', night='#D5EDF6',
                  tones=['#03303F', '#043E53', '#054C66', '#045C7C', '#016C93', '#007BA7', '#2C96BF', '#5FB3D4', '#93CDE4', '#C3E4F1']),
}


def cfg():
    return json.load(open(os.path.join(HERE, 'profile.json'), encoding='utf-8'))


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def svg(w, h, body, title='', extra_css=''):
    css = ("text{font-family:%s}.m{font-family:%s}" % (SANS, MONO)
           + "@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}" + extra_css
           + ("*{animation:none!important}.r,.bk{opacity:1!important}" if os.environ.get('STATIC') else ''))     # STATIC=1: frozen end state, for previews
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img"%s>'
            % (w, h, w, h, (' aria-label="%s"' % esc(title)) if title else '')
            + ('<title>%s</title>' % esc(title) if title else '') + '<style>%s</style>%s</svg>' % (css, body))


def save(name, text):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    return p


def both(name, fn):
    """fn(theme_dict, theme_name) -> svg text; writes assets/<name>-dark.svg and -light.svg"""
    for k, t in THEMES.items():
        save('%s-%s.svg' % (name, k), fn(t, k))


def icon_path(slug):
    """path data of a 24x24 simple-icons glyph stored in scripts/icons"""
    p = os.path.join(HERE, 'icons', slug + '.svg')
    if not os.path.exists(p):
        return None
    m = re.search(r'<path d="([^"]+)"', open(p, encoding='utf-8').read())
    return m.group(1) if m else None


def icon(slug, x, y, size, fill):
    d = icon_path(slug)
    if not d:
        return '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" stroke-width="1.5"/>' % (x + size / 2, y + size / 2, size / 2 - 1, fill)
    return '<path transform="translate(%.2f %.2f) scale(%.4f)" fill="%s" d="%s"/>' % (x, y, size / 24.0, fill, d)


# 5x7 block letters: the name is drawn from squares, so it looks the same on every system font
GLYPHS = {
    'A': ['01110', '10001', '10001', '11111', '10001', '10001', '10001'],
    'D': ['11110', '10001', '10001', '10001', '10001', '10001', '11110'],
    'W': ['10001', '10001', '10001', '10101', '10101', '11011', '10001'],
    'O': ['01110', '10001', '10001', '10001', '10001', '10001', '01110'],
    '0': ['01110', '10011', '10101', '10101', '10101', '11001', '01110'],
    '1': ['00100', '01100', '00100', '00100', '00100', '00100', '01110'],
    '2': ['01110', '10001', '00001', '00110', '01000', '10000', '11111'],
    '3': ['11110', '00001', '00001', '01110', '00001', '00001', '11110'],
    '4': ['00010', '00110', '01010', '10010', '11111', '00010', '00010'],
    '5': ['11111', '10000', '11110', '00001', '00001', '10001', '01110'],
    '6': ['01110', '10000', '11110', '10001', '10001', '10001', '01110'],
}


def blocks(text, x, y, px, gap, fill_fn, anim=False):
    """text in block letters; fill_fn(col_index_overall, row) -> colour. Returns (svg, width)."""
    out = []; cx = x; col0 = 0
    step = px + gap
    for ch in text:
        g = GLYPHS[ch]
        for r, row in enumerate(g):
            for c, v in enumerate(row):
                if v == '1':
                    st = (' style="animation-delay:%.2fs"' % (0.25 + 0.035 * (col0 + c) + 0.03 * r)) if anim else ''
                    out.append('<rect%s x="%.1f" y="%.1f" width="%d" height="%d" rx="%.1f" fill="%s"%s/>'
                               % (' class="bk"' if anim else '', cx + c * step, y + r * step, px, px, px * 0.18, fill_fn(col0 + c, r), st))
        cx += 5 * step + step; col0 += 6
    return ''.join(out), cx - step - gap - x


def lerp_hex(a, b, t):
    a = [int(a[i:i + 2], 16) for i in (1, 3, 5)]; b = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02X%02X%02X' % tuple(int(round(a[i] + (b[i] - a[i]) * max(0.0, min(1.0, t)))) for i in range(3))
