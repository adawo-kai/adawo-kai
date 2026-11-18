"""Parts that do not depend on live data: hero with the character portrait, link buttons, section headers, footer."""
import json, os
from common import *

DARK_RAMP = "~=+*x#%&@@"       # dark theme: dense everywhere so the hair stays a shape; the tone is carried by colour
LIGHT_RAMP = "@%#*+=~-:."      # light theme: a darker pixel gets a denser character


def hero(t, k):
    c = cfg()
    d = json.load(open(os.path.join(HERE, 'portrait.json')))
    H = 476
    px0, py0, cw, rh, fs = 24, 30, 4.15, 8.1, 7.2
    ramp = DARK_RAMP if k == 'dark' else LIGHT_RAMP
    rows = []
    for y, row in enumerate(d['lum']):
        last = max((i for i, v in enumerate(row) if v >= 0), default=-1)
        if last < 0:
            continue
        runs = []                       # [tone, text]; blanks ride along with the neighbouring run
        for v in row[:last + 1]:
            if v < 0:
                if runs:
                    runs[-1][1] += ' '
                else:
                    runs.append([0, ' '])
            elif runs and runs[-1][0] == v:
                runs[-1][1] += ramp[v]
            elif runs and not runs[-1][1].strip():
                runs[-1][0] = v; runs[-1][1] += ramp[v]
            else:
                runs.append([v, ramp[v]])
        n = sum(len(s) for _, s in runs)
        spans = ''.join('<tspan fill="%s">%s</tspan>' % (t['tones'][tone], esc(s)) for tone, s in runs)
        rows.append('<text class="r m" font-weight="700" style="animation-delay:%.2fs" x="%.1f" y="%.1f" font-size="%.1f" textLength="%.1f" lengthAdjust="spacing" '
                    'xml:space="preserve">%s</text>' % (0.02 * y, px0, py0 + (y + 1) * rh, fs, n * cw, spans))
    pw, ph = d['cols'] * cw, d['rows'] * rh
    body = ['<rect x="0.5" y="0.5" width="%d" height="%d" rx="16" fill="%s" stroke="%s"/>' % (W - 1, H - 1, t['panel'], t['line'])]
    body.append('<defs><linearGradient id="sg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s" stop-opacity="0"/>'
                '<stop offset=".5" stop-color="%s" stop-opacity=".16"/><stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient>'
                '<clipPath id="pc"><rect x="%.1f" y="%.1f" width="%.1f" height="%.1f"/></clipPath></defs>' % (t['glow'], t['glow'], t['glow'], px0, py0, pw, ph))
    body.append('<g>%s</g>' % ''.join(rows))
    body.append('<g clip-path="url(#pc)"><rect class="scan" x="%.1f" y="%.1f" width="%.1f" height="54" fill="url(#sg)"/></g>' % (px0, py0 - 54, pw))
    # right column
    x0 = 478
    body.append('<text class="m" x="%d" y="78" font-size="11.5" fill="%s" letter-spacing="1.2">github.com/%s</text>' % (x0, t['mute'], esc(c['login'])))
    grad = lambda col, r: lerp_hex(t['core'], t['hi'], col / 28.0)
    b, bw = blocks(c['name'], x0, 96, 10, 2, grad, anim=True)
    body.append(b)
    body.append('<text x="%d" y="222" font-size="21" font-weight="700" fill="%s">%s</text>' % (x0, t['ink'], esc(c['role'])))
    for i, ln in enumerate(c['tagline']):
        body.append('<text x="%d" y="%d" font-size="14.5" fill="%s">%s</text>' % (x0, 250 + i * 21, t['soft'], esc(ln)))
    for i, ln in enumerate(c['facts']):
        body.append('<text class="m" x="%d" y="%d" font-size="11.5" fill="%s" letter-spacing=".6" xml:space="preserve">%s</text>' % (x0, 316 + i * 20, t['hi'], esc(ln)))
    # heartbeat: a commit pulse that keeps running
    pts = [(0, 0), (58, 0), (68, -7), (78, 0), (120, 0), (130, 9), (141, -30), (153, 20), (163, 0), (214, 0), (224, -6), (234, 0), (300, 0), (344, 0)]
    path = 'M' + ' L'.join('%.1f %.1f' % (x0 + x, 392 + y) for x, y in pts)
    body.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.6" stroke-linejoin="round" opacity=".28"/>' % (path, t['hi']))
    body.append('<path class="beat" d="%s" fill="none" stroke="%s" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>' % (path, t['hi']))
    # palette signature
    for i, col in enumerate([t['tones'][1], t['tones'][3], t['core'], t['tones'][6], t['tones'][8]]):
        body.append('<rect x="%d" y="430" width="22" height="8" rx="4" fill="%s"/>' % (x0 + i * 28, col))
    body.append('<text class="m" x="%d" y="438" font-size="10.5" fill="%s" letter-spacing="1">cerulean #007BA7</text>' % (x0 + 152, t['mute']))
    css = ('.r{opacity:0;animation:rv .7s ease-out forwards}@keyframes rv{from{opacity:0}to{opacity:1}}'
           '.bk{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .55s cubic-bezier(.2,.9,.3,1.25) forwards}'
           '@keyframes pop{from{opacity:0;transform:scale(.2)}to{opacity:1;transform:scale(1)}}'
           '.scan{animation:sc 7s linear infinite}@keyframes sc{from{transform:translateY(0)}to{transform:translateY(%dpx)}}'
           '.beat{stroke-dasharray:70 520;animation:bt 3.6s linear infinite}@keyframes bt{from{stroke-dashoffset:590}to{stroke-dashoffset:0}}'
           '@media (prefers-reduced-motion:reduce){.r,.bk{opacity:1!important}.scan,.beat{display:none}}' % (ph + 60))
    return svg(W, H, ''.join(body), "%s — %s. Character portrait made from my photo." % (c['name'].title(), c['role']), css)


def button(link):
    def f(t, k):
        wide = 96 + max(len(link['label']) * 9.2, len(link['sub']) * 6.9) + 34
        w, h = int(wide), 60
        b = ['<rect x="0.5" y="0.5" width="%d" height="%d" rx="14" fill="%s" stroke="%s"/>' % (w - 1, h - 1, t['panel'], t['line'])]
        b.append('<rect x="11" y="11" width="38" height="38" rx="10" fill="%s"/>' % t['core'])
        b.append(icon(link['icon'], 19, 19, 22, '#FFFFFF'))
        b.append('<text x="62" y="27" font-size="15" font-weight="700" fill="%s">%s</text>' % (t['ink'], esc(link['label'])))
        b.append('<text class="m" x="62" y="45" font-size="11.3" fill="%s">%s</text>' % (t['soft'], esc(link['sub'])))
        ax = w - 26
        b.append('<path class="ar" d="M%d 35 l9 -9 M%d 26 h7 v7" fill="none" stroke="%s" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
                 % (ax, ax + 2, t['hi']))
        css = '.ar{animation:nudge 2.4s ease-in-out infinite}@keyframes nudge{0%,100%{transform:translate(0,0)}50%{transform:translate(2px,-2px)}}'
        return svg(w, h, ''.join(b), '%s: %s' % (link['label'], link['sub']), css)
    return f


def header(sec):
    def f(t, k):
        h = 66
        b = []
        num, nw = blocks(sec['num'], 2, 14, 5, 1, lambda c_, r: lerp_hex(t['core'], t['hi'], c_ / 11.0))
        b.append(num)
        tx = 2 + nw + 18
        b.append('<text x="%d" y="35" font-size="23" font-weight="700" fill="%s" letter-spacing=".2">%s</text>' % (tx, t['ink'], esc(sec['title'])))
        b.append('<text class="m" x="%d" y="55" font-size="11.3" fill="%s" letter-spacing=".5">%s</text>' % (tx, t['mute'], esc(sec['note'])))
        lx = tx + max(len(sec['title']) * 12.6, len(sec['note']) * 7.1) + 26
        b.append('<line x1="%d" y1="30" x2="%d" y2="30" stroke="%s" stroke-width="1"/>' % (lx, W - 14, t['line']))
        b.append('<circle class="dot" cx="%d" cy="30" r="3.5" fill="%s"/>' % (W - 8, t['hi']))
        for i in range(1, 9):
            x = lx + (W - 14 - lx) * i / 9.0
            b.append('<line x1="%.1f" y1="27" x2="%.1f" y2="33" stroke="%s" stroke-width="1"/>' % (x, x, t['line']))
        css = '.dot{animation:bl 2.8s ease-in-out infinite}@keyframes bl{0%,100%{opacity:1}50%{opacity:.25}}'
        return svg(W, h, ''.join(b), '%s — %s' % (sec['num'], sec['title']), css)
    return f


def footer(t, k):
    import math
    h = 86
    b = []
    for j, (amp, per, op, sw) in enumerate(((9, 190, .9, 1.6), (6, 140, .55, 1.2), (4, 96, .35, 1.0))):
        pts = ' '.join('%.1f,%.1f' % (x, 30 + j * 9 + amp * math.sin(x / per * 2 * math.pi + j * 1.3)) for x in range(0, W + 6, 6))
        b.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="%.1f" opacity="%.2f"/>' % (pts, t['tones'][4 + j * 2 if k == 'dark' else 5 - j], sw, op))
    b.append('<text class="m" x="%d" y="76" font-size="11" fill="%s" text-anchor="middle" letter-spacing="1.5">'
             'drawn by code in this repository  /  no trackers  /  cerulean all the way down</text>' % (W // 2, t['mute']))
    return svg(W, h, ''.join(b), 'End of profile')


def stack(t, k):
    c = cfg()
    tw, th, gap, x0, per = 130, 34, 9, 140, 5
    y = 22; b = []; n_all = 0
    for g in c['stack']:
        rows = (len(g['items']) + per - 1) // per
        b.append('<text class="m" x="22" y="%d" font-size="11.5" font-weight="700" fill="%s" letter-spacing="1">%s</text>' % (y + 21, t['hi'], esc(g['group'])))
        b.append('<text class="m" x="22" y="%d" font-size="10" fill="%s">%02d</text>' % (y + 36, t['mute'], len(g['items'])))
        for i, (name, slug) in enumerate(g['items']):
            x = x0 + (i % per) * (tw + gap); yy = y + (i // per) * (th + gap)
            b.append('<g class="tl" style="animation-delay:%.2fs"><rect x="%d" y="%d" width="%d" height="%d" rx="9" fill="%s" stroke="%s"/>' % (0.03 * n_all, x, yy, tw, th, t['panel2'], t['line']))
            if slug and icon_path(slug):
                b.append(icon(slug, x + 10, yy + 9, 16, t['hi']))
            else:
                b.append('<rect x="%d" y="%d" width="16" height="16" rx="4" fill="none" stroke="%s" stroke-width="1.3"/><text class="m" x="%d" y="%d" font-size="7.6" font-weight="700" fill="%s" text-anchor="middle">%s</text>'
                         % (x + 10, yy + 9, t['hi'], x + 18, yy + 20, t['hi'], esc(name[:2].upper())))
            b.append('<text x="%d" y="%d" font-size="12.4" font-weight="600" fill="%s">%s</text></g>' % (x + 33, yy + 22, t['ink'], esc(name)))
            n_all += 1
        y += rows * (th + gap) + 12
        if g is not c['stack'][-1]:
            b.append('<line x1="22" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-dasharray="2 5"/>' % (y - 6, W - 22, y - 6, t['line']))
            y += 8
    H = y + 12
    frame = '<rect x="0.5" y="0.5" width="%d" height="%d" rx="16" fill="%s" stroke="%s"/>' % (W - 1, H - 1, t['panel'], t['line'])
    css = '.tl{animation:ti .5s ease-out both}@keyframes ti{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}'
    names = '; '.join('%s: %s' % (g['group'], ', '.join(n for n, _ in g['items'])) for g in c['stack'])
    return svg(W, H, frame + ''.join(b), 'Stack. ' + names, css)


def build():
    c = cfg()
    both('hero', hero)
    both('stack', stack)
    for ln in c['links']:
        both('btn-' + ln['id'], button(ln))
    for sec in c['sections']:
        both('h-' + sec['id'], header(sec))
    both('footer', footer)
