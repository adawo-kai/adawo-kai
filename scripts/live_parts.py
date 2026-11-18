"""Parts drawn from live data: the room, the commit mountains, the numbers, repository cards. Standard library only."""
import datetime, math, os, random, textwrap
from common import *
import data as D

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def facts(d, c):
    """everything the drawings need, derived once"""
    utc = datetime.datetime.now(datetime.timezone.utc)
    now = utc + datetime.timedelta(hours=c['utc_offset_hours'])
    days = d['days']
    week7 = sum(x['n'] for x in days[-7:])
    streak = 0
    for x in reversed(days if days[-1]['n'] else days[:-1]):
        if not x['n']:
            break
        streak += 1
    best = max(d['weeks'], key=lambda w: w['n'])
    own = [r for r in d['repos'] if not r['fork']]
    last = d['repos'][0] if d['repos'] else None
    ago = None
    if last:
        ago = (utc - datetime.datetime.fromisoformat(last['pushed'].replace('Z', '+00:00'))).days
    h = now.hour + now.minute / 60.0
    phase = 'night' if (h < 5.5 or h >= 19.5) else 'dawn' if h < 7.5 else 'day' if h < 17.5 else 'dusk'
    sky = 'overcast' if week7 == 0 else 'cloudy' if week7 < 4 else 'a few clouds' if week7 < 10 else 'clear'
    tot = float(sum(d['langs'].values()) or 1)
    langs = [kv for kv in sorted(((k, v / tot) for k, v in d['langs'].items()), key=lambda kv: -kv[1]) if kv[1] >= 0.02]      # below 2 % is noise
    return dict(now=now, hour=h, phase=phase, week7=week7, today=days[-1]['n'], streak=streak, best=best, last=last, ago=ago, sky=sky,
                langs=langs, own=own, clouds={'overcast': 5, 'cloudy': 3, 'a few clouds': 1, 'clear': 0}[sky])


def ago_text(n):
    return 'today' if n == 0 else 'yesterday' if n == 1 else '%d days ago' % n if n < 60 else '%d months ago' % (n // 30)


SKY = {'night': ('#03131C', '#0B3A52'), 'dawn': ('#0A4764', '#A8E1F7'), 'day': ('#1794C4', '#D3F1FB'), 'dusk': ('#062C40', '#45BAE5')}


def celestial(f, x0, y0, w, h, rnd, small=False):
    """sun or moon and stars for the current local time, inside a box"""
    out = []
    night = f['phase'] == 'night'
    if night or f['phase'] == 'dusk':
        for i in range(34 if night else 10):
            sx = x0 + rnd.uniform(6, w - 6); sy = y0 + rnd.uniform(5, h * 0.62); r = rnd.choice((0.7, 0.9, 1.2, 1.5))
            out.append('<circle class="tw" style="animation-delay:%.1fs" cx="%.1f" cy="%.1f" r="%.1f" fill="#E6F8FE"/>' % (rnd.uniform(0, 4), sx, sy, r))
    if night:
        mx, my, mr = x0 + w * 0.74, y0 + h * 0.26, (11 if small else 15)
        out.append('<circle cx="%.1f" cy="%.1f" r="%d" fill="#E6F8FE" opacity=".12"/>' % (mx, my, mr + 9))
        out.append('<path d="M%.1f %.1f a%d %d 0 1 0 %.1f %.1f a%.1f %.1f 0 0 1 %.1f %.1f z" fill="#E6F8FE"/>'
                   % (mx + mr * 0.2, my - mr, mr, mr, mr * 0.75, mr * 1.55, mr * 0.82, mr * 0.82, -mr * 0.75, -mr * 1.55))
    else:
        t = (f['hour'] - 5.5) / 14.0                        # 0 at dawn .. 1 at dusk
        sx = x0 + w * (0.12 + 0.76 * t); sy = y0 + h * (0.62 - 0.44 * math.sin(max(0.0, min(1.0, t)) * math.pi))
        r = 12 if small else 16
        out.append('<circle class="sun" cx="%.1f" cy="%.1f" r="%d" fill="#F3FCFF" opacity=".22"/>' % (sx, sy, r + 12))
        out.append('<circle cx="%.1f" cy="%.1f" r="%d" fill="#F3FCFF"/>' % (sx, sy, r))
    return ''.join(out)


def cloud(x, y, s, fill, op, cls, delay):
    return ('<g class="%s" style="animation-delay:%.1fs" opacity="%.2f" fill="%s"><ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f"/>'
            '<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f"/><ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f"/></g>'
            % (cls, delay, op, fill, x, y, 26 * s, 9 * s, x - 14 * s, y - 6 * s, 14 * s, 9 * s, x + 10 * s, y - 8 * s, 17 * s, 11 * s))


def room(d, f):
    def draw(t, k):
        H = 344
        rnd = random.Random(7)
        night = f['phase'] in ('night', 'dusk')
        b = ['<rect x="0.5" y="0.5" width="%d" height="%d" rx="16" fill="%s" stroke="%s"/>' % (W - 1, H - 1, t['panel'], t['line'])]
        b.append('<path d="M1 268 H%d V%d a15 15 0 0 1 -15 15 H16 a15 15 0 0 1 -15 -15 z" fill="%s"/>' % (W - 1, H - 16, t['panel2']))
        b.append('<line x1="1" y1="268" x2="%d" y2="268" stroke="%s"/>' % (W - 1, t['line']))
        # ---- window: the sky is my local time, the clouds are my commits
        wx, wy, ww, wh = 44, 40, 250, 184
        top, bot = SKY[f['phase']]
        b.append('<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>'
                 '<clipPath id="wc"><rect x="%d" y="%d" width="%d" height="%d" rx="6"/></clipPath>'
                 '<linearGradient id="cone" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s" stop-opacity=".34"/><stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient></defs>'
                 % (top, bot, wx, wy, ww, wh, t['glow'] if k == 'dark' else '#35B6E6', t['glow'] if k == 'dark' else '#35B6E6'))
        b.append('<g clip-path="url(#wc)"><rect x="%d" y="%d" width="%d" height="%d" fill="url(#sky)"/>' % (wx, wy, ww, wh))
        b.append(celestial(f, wx, wy, ww, wh, rnd))
        if f['today'] and f['phase'] == 'night':
            b.append('<line class="shoot" x1="%d" y1="%d" x2="%d" y2="%d" stroke="#E6F8FE" stroke-width="1.6" stroke-linecap="round"/>' % (wx + 150, wy + 30, wx + 190, wy + 46))
        ccol = '#CDEBF6' if f['phase'] in ('day', 'dawn') else '#2B6E8C'
        for i in range(f['clouds']):
            b.append(cloud(wx + 30 + i * 52 + rnd.uniform(-8, 8), wy + 34 + (i % 3) * 22 + rnd.uniform(-5, 5), rnd.uniform(0.9, 1.35), ccol, 0.92, 'drift', -i * 3.0))
        ridge = lambda yb, amp, seed, n=9: ' '.join('%.1f,%.1f' % (wx + ww * i / n, wy + wh - yb - amp * abs(math.sin(i * 1.7 + seed))) for i in range(n + 1))
        mcol = ('#0A4764', '#05283A') if f['phase'] in ('night', 'dusk') else ('#3FA6CE', '#0A6A8F')
        b.append('<polygon points="%d,%d %s %d,%d" fill="%s"/>' % (wx, wy + wh, ridge(30, 46, 0.4), wx + ww, wy + wh, mcol[0]))
        b.append('<polygon points="%d,%d %s %d,%d" fill="%s"/>' % (wx, wy + wh, ridge(10, 34, 2.1, 7), wx + ww, wy + wh, mcol[1]))
        b.append('</g>')
        fr = t['line'] if k == 'dark' else '#8FC7DC'
        b.append('<rect x="%d" y="%d" width="%d" height="%d" rx="6" fill="none" stroke="%s" stroke-width="5"/>' % (wx, wy, ww, wh, fr))
        b.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="3"/>' % (wx + ww // 2, wy, wx + ww // 2, wy + wh, fr))
        b.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="3"/>' % (wx, wy + wh * 0.42, wx + ww, wy + wh * 0.42, fr))
        b.append('<rect x="%d" y="%d" width="%d" height="8" rx="3" fill="%s"/>' % (wx - 8, wy + wh + 2, ww + 16, fr))
        # ---- wall clock: the minute this picture was drawn
        cx, cy, cr = 346, 76, 26
        b.append('<circle cx="%d" cy="%d" r="%d" fill="%s" stroke="%s" stroke-width="2.5"/>' % (cx, cy, cr, t['panel2'], t['core']))
        for i in range(12):
            a = i * math.pi / 6
            b.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%.1f"/>'
                     % (cx + math.sin(a) * (cr - 6), cy - math.cos(a) * (cr - 6), cx + math.sin(a) * (cr - 3), cy - math.cos(a) * (cr - 3), t['mute'], 1.6 if i % 3 == 0 else 0.9))
        ha = (f['hour'] % 12) / 12.0 * 2 * math.pi; ma = f['now'].minute / 60.0 * 2 * math.pi
        b.append('<line x1="%d" y1="%d" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="3" stroke-linecap="round"/>' % (cx, cy, cx + math.sin(ha) * 12, cy - math.cos(ha) * 12, t['ink']))
        b.append('<line x1="%d" y1="%d" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="2" stroke-linecap="round"/>' % (cx, cy, cx + math.sin(ma) * 18, cy - math.cos(ma) * 18, t['hi']))
        b.append('<circle cx="%d" cy="%d" r="2.5" fill="%s"/>' % (cx, cy, t['hi']))
        # ---- tear-off calendar
        kx, ky = 318, 126
        b.append('<rect x="%d" y="%d" width="58" height="68" rx="7" fill="%s" stroke="%s"/>' % (kx, ky, t['panel2'], t['line']))
        b.append('<path d="M%d %d h44 a7 7 0 0 1 7 7 v11 h-58 v-11 a7 7 0 0 1 7 -7 z" fill="%s"/>' % (kx + 7, ky, t['core']))
        b.append('<text class="m" x="%d" y="%d" font-size="10" font-weight="700" fill="#FFFFFF" text-anchor="middle" letter-spacing="1.5">%s</text>'
                 % (kx + 29, ky + 13, MONTHS[f['now'].month - 1].upper()))
        b.append('<text x="%d" y="%d" font-size="26" font-weight="700" fill="%s" text-anchor="middle">%d</text>' % (kx + 29, ky + 46, t['ink'], f['now'].day))
        b.append('<text class="m" x="%d" y="%d" font-size="9.5" fill="%s" text-anchor="middle">7d: %d</text>' % (kx + 29, ky + 60, t['mute'], f['week7']))
        # ---- shelf: one book per language, as tall as its share of my code; the plant grows with contributions
        sx0, sy = 420, 128
        b.append('<rect x="%d" y="%d" width="390" height="6" rx="3" fill="%s"/>' % (sx0, sy, fr))
        x = sx0 + 16
        top5 = [x_ for x_ in f['langs'][:5] if x_[1] >= 0.03]
        for i, (name, share) in enumerate(top5):
            bh = 34 + 50 * math.sqrt(share / max(top5[0][1], 1e-6)); bw = 27 if i % 2 == 0 else 23
            col = t['tones'][[7, 5, 4, 3, 6, 2][i]] if k == 'dark' else t['tones'][[2, 4, 5, 6, 3, 7][i]]
            lean = 0
            b.append('<g transform="rotate(%d %.1f %d)"><rect x="%.1f" y="%.1f" width="%d" height="%.1f" rx="2.5" fill="%s"/>'
                     '<rect x="%.1f" y="%.1f" width="%d" height="2" fill="%s" opacity=".5"/>'
                     '<text class="m" transform="translate(%.1f %.1f) rotate(-90)" font-size="9.6" font-weight="700" fill="%s">%s</text></g>'
                     % (lean, x + bw, sy, x, sy - bh, bw, bh, col, x, sy - bh + 6, bw, t['panel'], x + bw / 2 + 3, sy - 6,
                        t['night'] if k == 'dark' else '#FFFFFF', esc(name[:10])))
            x += bw + 3
        px = sx0 + 332
        leaves = min(12, 3 + d['total'] // 12)
        b.append('<path d="M%d %d h34 l-5 26 h-24 z" fill="%s"/>' % (px - 17, sy - 26, t['core']))
        for i in range(leaves):
            a = -math.pi / 2 + (i - (leaves - 1) / 2.0) * 0.32
            ln = 26 + 14 * ((i * 7) % 5) / 4.0
            ex, ey = px + math.cos(a) * ln, sy - 26 + math.sin(a) * ln
            b.append('<path class="leaf" style="animation-delay:%.1fs" d="M%d %d Q%.1f %.1f %.1f %.1f Q%.1f %.1f %d %d z" fill="%s"/>'
                     % (i * 0.3, px, sy - 26, px + math.cos(a - 0.5) * ln * 0.6, sy - 26 + math.sin(a - 0.5) * ln * 0.6, ex, ey,
                        px + math.cos(a + 0.5) * ln * 0.6, sy - 26 + math.sin(a + 0.5) * ln * 0.6, px, sy - 26, t['tones'][6 if i % 2 else 4]))
        # ---- desk, monitor with the last push, lamp, cup
        dy = 240
        b.append('<rect x="392" y="%d" width="430" height="9" rx="4" fill="%s"/>' % (dy, fr))
        for lx in (410, 796):
            b.append('<rect x="%d" y="%d" width="7" height="58" fill="%s"/>' % (lx, dy + 9, fr))
        mx, my, mw, mh = 478, 150, 214, 78
        asleep = f['ago'] is None or f['ago'] > 14
        b.append('<rect x="%d" y="%d" width="%d" height="%d" rx="9" fill="%s" stroke="%s" stroke-width="3"/>' % (mx, my, mw, mh, '#04161F' if k == 'dark' else '#0B2A36', fr))
        b.append('<rect x="%d" y="%d" width="10" height="10" fill="%s"/><rect x="%d" y="%d" width="62" height="5" rx="2" fill="%s"/>' % (mx + mw // 2 - 5, my + mh, fr, mx + mw // 2 - 31, dy - 5, fr))
        if f['last']:
            r = f['last']
            b.append('<text class="m" x="%d" y="%d" font-size="10" fill="#7FAFC2">$ git log -1 --all</text>' % (mx + 13, my + 20))
            b.append('<text class="m" x="%d" y="%d" font-size="12.5" font-weight="700" fill="#63C6EA">%s</text>' % (mx + 13, my + 39, esc(r['name'][:24])))
            b.append('<text class="m" x="%d" y="%d" font-size="10.5" fill="#BFDCE7">%s  /  pushed %s</text>' % (mx + 13, my + 55, esc(r['lang'] or 'docs'), ago_text(f['ago'])))
            b.append('<text class="m" x="%d" y="%d" font-size="10" fill="#7FAFC2">$</text><rect class="cur" x="%d" y="%d" width="6" height="11" fill="#63C6EA"/>'
                     % (mx + 13, my + 70, mx + 24, my + 61))
        if asleep:
            b.append('<text class="m zz" x="%d" y="%d" font-size="10" fill="#7FAFC2" text-anchor="end">asleep  z z z</text>' % (mx + mw - 13, my + 70))
        lx = 428
        b.append('<rect x="%d" y="%d" width="34" height="5" rx="2" fill="%s"/>' % (lx - 17, dy - 5, t['core']))
        b.append('<path d="M%d %d L%d %d L%d %d" fill="none" stroke="%s" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>' % (lx, dy - 5, lx - 8, dy - 46, lx + 16, dy - 70, t['core']))
        if night:
            b.append('<polygon class="glowc" points="%d,%d %d,%d %d,%d %d,%d" fill="url(#cone)"/>' % (lx + 6, dy - 62, lx + 34, dy - 62, lx + 96, dy, lx - 40, dy))
        b.append('<path d="M%d %d l30 0 l8 14 l-46 0 z" fill="%s"/>' % (lx + 5, dy - 78, t['hi'] if night else t['deep']))
        ux, uy = 726, dy
        b.append('<path d="M%d %d h30 l-3 22 a4 4 0 0 1 -4 3 h-16 a4 4 0 0 1 -4 -3 z" fill="%s"/><path d="M%d %d a8 8 0 0 1 0 14" fill="none" stroke="%s" stroke-width="3"/>'
                 % (ux - 15, uy - 25, t['ink'] if k == 'dark' else '#FFFFFF', ux + 14, uy - 20, t['ink'] if k == 'dark' else '#FFFFFF'))
        if k == 'light':
            b.append('<path d="M%d %d h30 l-3 22 a4 4 0 0 1 -4 3 h-16 a4 4 0 0 1 -4 -3 z" fill="none" stroke="%s" stroke-width="1.6"/>' % (ux - 15, uy - 25, t['core']))
        for i in range(3):
            b.append('<path class="steam" style="animation-delay:%.1fs" d="M%d %d q5 -7 0 -14 q-5 -7 0 -14" fill="none" stroke="%s" stroke-width="1.8" stroke-linecap="round"/>'
                     % (i * 0.9, ux - 8 + i * 8, uy - 30, t['soft']))
        # ---- status line
        st = '%02d:%02d utc%+d  /  %s  /  sky: %s (%d contribution%s in 7 days)' % (f['now'].hour, f['now'].minute, cfg()['utc_offset_hours'], f['phase'],
                                                                                    f['sky'], f['week7'], '' if f['week7'] == 1 else 's')
        b.append('<text class="m" x="24" y="%d" font-size="11.3" fill="%s" letter-spacing=".4">%s</text>' % (H - 22, t['soft'], esc(st)))
        b.append('<circle class="live" cx="%d" cy="%d" r="4" fill="%s"/><text class="m" x="%d" y="%d" font-size="11.3" fill="%s" text-anchor="end">live</text>'
                 % (W - 28, H - 26, t['hi'], W - 40, H - 22, t['hi']))
        css = ('.tw{animation:tw 3.2s ease-in-out infinite}@keyframes tw{0%,100%{opacity:1}50%{opacity:.15}}'
               '.drift{animation:dr 26s linear infinite alternate}@keyframes dr{from{transform:translateX(-16px)}to{transform:translateX(22px)}}'
               '.sun{animation:pu 4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}@keyframes pu{0%,100%{transform:scale(1)}50%{transform:scale(1.25)}}'
               '.cur{animation:cb 1.1s steps(1) infinite}@keyframes cb{50%{opacity:0}}'
               '.steam{animation:stm 2.7s ease-out infinite;opacity:0}@keyframes stm{0%{opacity:0;transform:translateY(4px)}40%{opacity:.8}100%{opacity:0;transform:translateY(-12px)}}'
               '.leaf{animation:lf 5s ease-in-out infinite;transform-box:fill-box;transform-origin:bottom center}@keyframes lf{0%,100%{transform:rotate(-1.5deg)}50%{transform:rotate(2deg)}}'
               '.glowc{animation:gl 5s ease-in-out infinite}@keyframes gl{0%,100%{opacity:1}50%{opacity:.75}}'
               '.live{animation:lv 1.8s ease-in-out infinite}@keyframes lv{0%,100%{opacity:1}50%{opacity:.2}}'
               '.zz{animation:lv 3s ease-in-out infinite}'
               '.shoot{stroke-dasharray:44;animation:sh 6s ease-in infinite}@keyframes sh{0%,70%{stroke-dashoffset:44;opacity:0}75%{opacity:1}100%{stroke-dashoffset:-44;opacity:0}}')
        return svg(W, H, ''.join(b), 'My room right now: %s, %s sky, last push to %s %s' % (f['phase'], f['sky'], f['last']['name'] if f['last'] else '-', ago_text(f['ago'] or 0)), css)
    return draw


def mountains(d, f):
    def draw(t, k):
        H = 286
        rnd = random.Random(11)
        weeks = d['weeks']; n = len(weeks)
        mxn = max(1, max(w['n'] for w in weeks))
        X = lambda i: 26 + (W - 52) * i / float(n - 1)
        base = 226
        b = ['<rect x="0.5" y="0.5" width="%d" height="%d" rx="16" fill="%s" stroke="%s"/>' % (W - 1, H - 1, t['panel'], t['line'])]
        b.append('<defs><clipPath id="mc"><rect x="1" y="1" width="%d" height="%d" rx="15"/></clipPath>'
                 '<linearGradient id="msky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s" stop-opacity="%s"/><stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient></defs>'
                 % (W - 2, H - 2, SKY[f['phase']][0] if k == 'dark' else SKY['day'][0], '.9' if k == 'dark' else '.16', t['panel']))
        b.append('<g clip-path="url(#mc)"><rect x="1" y="1" width="%d" height="200" fill="url(#msky)"/>' % (W - 2))
        ff = dict(f)
        if k == 'light' and f['phase'] in ('night', 'dusk'):
            ff = dict(f, phase='day', hour=12.0)               # the light page keeps a daytime sky so it stays light
        b.append(celestial(ff, 26, 46, W - 52, 150, rnd, small=True))
        peak = [18 + 12 * abs(math.sin(i * 0.9)) + 150 * math.sqrt(w['n'] / float(mxn)) for i, w in enumerate(weeks)]
        smooth = [sum(peak[max(0, i - 3):i + 4]) / len(peak[max(0, i - 3):i + 4]) for i in range(n)]
        far = ' '.join('%.1f,%.1f' % (X(i), base - 34 - smooth[i] * 0.62 - 9 * math.sin(i * 0.55)) for i in range(n))
        b.append('<polygon points="26,%d %s %d,%d" fill="%s"/>' % (base + 30, far, W - 26, base + 30, t['tones'][1 if k == 'dark' else 8]))
        peak = [14 + 10 * abs(math.sin(i * 0.9)) + 128 * math.sqrt(w['n'] / float(mxn)) for i, w in enumerate(weeks)]
        pts = []                                   # every week is a cone about two weeks wide on each side, so peaks read as mountains, not needles
        for q in range((n - 1) * 4 + 1):
            xi = q / 4.0
            hgt = max(peak[j] * max(0.0, 1 - abs(xi - j) / (2.6 if weeks[j]['n'] else 1.6)) for j in range(max(0, int(xi) - 3), min(n, int(xi) + 5)))
            pts.append((X(xi), base - hgt - (rnd.uniform(-2.2, 2.2) if q % 4 else 0)))
        b.append('<polygon points="26,%d %s %d,%d" fill="%s"/>' % (base + 30, ' '.join('%.1f,%.1f' % p for p in pts), W - 26, base + 30, t['tones'][3 if k == 'dark' else 6]))
        thr = sorted(w['n'] for w in weeks)[int(n * 0.8)]
        for i, w in enumerate(weeks):
            if w['n'] and w['n'] >= max(thr, 1) and all(peak[i] >= peak[j] for j in range(max(0, i - 2), min(n, i + 3))):
                x, y = X(i), base - peak[i]
                b.append('<polygon points="%.1f,%.1f %.1f,%.1f %.1f,%.1f %.1f,%.1f %.1f,%.1f" fill="%s"/>'
                         % (x, y, x - 6.4, y + 17, x - 2.4, y + 12.5, x + 1.6, y + 18, x + 6.4, y + 16, '#E6F8FE' if k == 'dark' else '#FFFFFF'))
        hill = ' '.join('%.1f,%.1f' % (x, base + 4 - 9 * math.sin(x / 70.0) - 6 * math.sin(x / 23.0 + 1)) for x in range(0, W + 8, 8))
        b.append('<polygon points="0,%d %s %d,%d" fill="%s"/>' % (H, hill, W, H, t['tones'][0] if k == 'dark' else t['tones'][3]))
        for i in range(len(f['own'])):                          # one tree per repository of mine
            x = 30 + (W - 60) * ((i * 0.6180339) % 1.0); s = rnd.uniform(0.8, 1.35)
            y = base + 6 - 9 * math.sin(x / 70.0) - 6 * math.sin(x / 23.0 + 1)
            b.append('<path d="M%.1f %.1f l%.1f %.1f h%.1f z" fill="%s"/>' % (x, y - 13 * s, 4.6 * s, 13 * s, -9.2 * s, t['tones'][4] if k == 'dark' else t['tones'][0]))
        for i in range(2):
            b.append(cloud(210 + i * 250, 76 + i * 26, 1.5, '#E6F8FE' if k == 'dark' else '#FFFFFF', 0.10 if k == 'dark' else 0.9, 'drift', -i * 9.0))
        b.append('</g>')
        last_m = None
        for i, w in enumerate(weeks):
            m = int(w['start'][5:7])
            if m != last_m and 0 < i < n - 2:
                b.append('<text class="m" x="%.1f" y="%d" font-size="9.5" fill="%s">%s</text>' % (X(i), H - 12, t['soft'] if k == 'dark' else '#FFFFFF', MONTHS[m - 1].lower()))
            last_m = m
        bi = max(range(n), key=lambda i: weeks[i]['n'])
        bx, by = X(bi), base - peak[bi]
        right = bx < W - 250
        b.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1" stroke-dasharray="2 3"/>' % (bx, by - 4, bx, 38, t['hi']))
        b.append('<circle class="pk" cx="%.1f" cy="%.1f" r="3.5" fill="%s"/>' % (bx, by - 2, t['hi']))
        b.append('<text class="m" x="%.1f" y="34" font-size="10.8" fill="%s" text-anchor="%s">best week: %d contributions, %s %s</text>'
                 % (bx + (8 if right else -8), t['ink'], 'start' if right else 'end', weeks[bi]['n'], MONTHS[int(weeks[bi]['start'][5:7]) - 1], weeks[bi]['start'][:4]))
        b.append('<text class="m" x="%d" y="%d" font-size="10.8" fill="%s" text-anchor="%s">%d contributions in a year  /  %d trees = %d repositories</text>'
                 % ((W - 24, 34, t['soft'], 'end', d['total'], len(f['own']), len(f['own'])) if not right or bx < W - 560 else (24, 34, t['soft'], 'start', d['total'], len(f['own']), len(f['own']))))
        css = ('.tw{animation:tw 3.2s ease-in-out infinite}@keyframes tw{0%,100%{opacity:1}50%{opacity:.15}}'
               '.drift{animation:dr 40s linear infinite alternate}@keyframes dr{from{transform:translateX(-30px)}to{transform:translateX(40px)}}'
               '.sun{animation:pu 4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}@keyframes pu{0%,100%{transform:scale(1)}50%{transform:scale(1.25)}}'
               '.pk{animation:pk 2.2s ease-in-out infinite}@keyframes pk{0%,100%{opacity:1}50%{opacity:.3}}')
        return svg(W, H, ''.join(b), 'My last year of contributions drawn as a mountain range: every week is a peak, every repository a tree', css)
    return draw


def numbers(d, f):
    def draw(t, k):
        H = 150
        b = []
        items = [(str(len(d['repos'])), 'public repositories'), (str(d['total']), 'contributions, last year'),
                 (str(f['best']['n']), 'best week'), (d['since'][:4], 'on github since')]
        tw = (W - 3 * 14) / 4.0
        for i, (num, lab) in enumerate(items):
            x = i * (tw + 14)
            b.append('<rect x="%.1f" y="0.5" width="%.1f" height="78" rx="13" fill="%s" stroke="%s"/>' % (x + 0.5, tw - 1, t['panel'], t['line']))
            b.append('<text x="%.1f" y="42" font-size="30" font-weight="700" fill="%s">%s</text>' % (x + 18, t['hi'], esc(num)))
            b.append('<text class="m" x="%.1f" y="63" font-size="10.5" fill="%s" letter-spacing=".4">%s</text>' % (x + 18, t['mute'], esc(lab)))
        langs = f['langs'][:6]
        tot = sum(s for _, s in langs) or 1.0
        x = 0.0; order = [4, 6, 2, 8, 3, 7] if k == 'dark' else [5, 2, 7, 0, 4, 8]
        b.append('<clipPath id="lb"><rect x="0" y="98" width="%d" height="12" rx="6"/></clipPath><g clip-path="url(#lb)">' % W)
        for i, (name, s) in enumerate(langs):
            w = W * s / tot
            b.append('<rect x="%.1f" y="98" width="%.1f" height="12" fill="%s"/>' % (x, w + 0.5, t['tones'][order[i]]))
            x += w
        b.append('</g>')
        x = 0.0
        for i, (name, s) in enumerate(langs):
            lab = '%s %d%%' % (name, round(100 * s / tot))
            b.append('<circle cx="%.1f" cy="131" r="4.5" fill="%s"/><text class="m" x="%.1f" y="135" font-size="11" fill="%s">%s</text>' % (x + 5, t['tones'][order[i]], x + 15, t['soft'], esc(lab)))
            x += 28 + len(lab) * 6.9
        return svg(W, H, ''.join(b), 'Numbers: %s public repositories, %s contributions in the last year. Languages: %s'
                   % (items[0][0], items[1][0], ', '.join('%s %d%%' % (n_, round(100 * s / tot)) for n_, s in langs)))
    return draw


def card(r):
    def draw(t, k):
        w, h = 414, 150
        b = ['<rect x="0.5" y="0.5" width="%d" height="%d" rx="14" fill="%s" stroke="%s"/>' % (w - 1, h - 1, t['panel'], t['line'])]
        b.append('<path d="M20 22 v15 a3 3 0 0 0 3 3 h9" fill="none" stroke="%s" stroke-width="1.8" stroke-linecap="round"/><circle cx="20" cy="20" r="3.4" fill="%s"/><circle cx="35" cy="40" r="3.4" fill="%s"/>'
                 % (t['hi'], t['hi'], t['hi']))
        b.append('<text class="m" x="48" y="36" font-size="15.5" font-weight="700" fill="%s">%s</text>' % (t['ink'], esc(r['name'][:30])))
        lines = textwrap.wrap(r['desc'] or 'No description yet.', 54)[:3]
        if len(textwrap.wrap(r['desc'] or '', 54)) > 3:
            lines[-1] = lines[-1][:51].rstrip() + '...'
        for i, ln in enumerate(lines):
            b.append('<text x="20" y="%d" font-size="12.6" fill="%s">%s</text>' % (66 + i * 18, t['soft'], esc(ln)))
        b.append('<circle cx="25" cy="%d" r="5" fill="%s"/><text class="m" x="36" y="%d" font-size="11" fill="%s">%s</text>' % (h - 22, t['core'], h - 18, t['soft'], esc(r['lang'] or 'docs')))
        tail = 'pushed %s %s' % (MONTHS[int(r['pushed'][5:7]) - 1], r['pushed'][:4])
        if r['stars']:
            tail = '%d star%s  /  ' % (r['stars'], '' if r['stars'] == 1 else 's') + tail
        b.append('<text class="m" x="%d" y="%d" font-size="11" fill="%s" text-anchor="end">%s</text>' % (w - 20, h - 18, t['mute'], esc(tail)))
        return svg(w, h, ''.join(b), '%s: %s' % (r['name'], r['desc']))
    return draw


def featured(d):
    own = [r for r in d['repos'] if not r['fork'] and r['desc']]
    own.sort(key=lambda r: (-r['stars'], -(len(r['desc']) >= 30), r['pushed'] and -int(r['pushed'][:10].replace('-', ''))))
    picks = cfg().get('featured')
    if picks:                                   # hand-picked, with an English line for the card; anything missing falls back to the automatic order
        by = {r['name']: r for r in d['repos']}
        out = [dict(by[p_['name']], desc=p_.get('desc') or by[p_['name']]['desc']) for p_ in picks if p_['name'] in by]
        out += [r for r in own if r['name'] not in {x['name'] for x in out}]
        return out[:4]
    return own[:4]


def snake(d, f):
    """my own contribution snake: it runs a closed serpentine lap over the last year, eats what it passes, the cells grow back half a lap later"""
    def draw(t, k):
        days = d['days']
        y0, m0, d0 = (int(v) for v in days[0]['date'].split('-'))
        off = (datetime.date(y0, m0, d0).weekday() + 1) % 7          # rows are weekdays, Sunday on top, like GitHub's own graph
        cols = (len(days) + off + 6) // 7
        cell, gap = 11, 4; step = cell + gap
        gx = (W - cols * step + gap) / 2.0; gy = 34
        H = gy + 7 * step + 46
        nz = sorted(x['n'] for x in days if x['n'])
        qs = [nz[int(len(nz) * q)] for q in (0.25, 0.5, 0.75)] if nz else [1, 2, 3]
        lev = lambda n: 0 if n == 0 else 1 + sum(n > q for q in qs)
        pal = [t['panel2'], t['tones'][2], t['tones'][4], t['tones'][6], t['tones'][8]] if k == 'dark' else [t['panel2'], t['tones'][8], t['tones'][6], t['tones'][5], t['tones'][2]]
        cen = lambda c_, r: (gx + c_ * step + cell / 2.0, gy + r * step + cell / 2.0)
        route = []; dist = {}; total = 0.0
        for c_ in range(cols):
            for r in (range(7) if c_ % 2 == 0 else range(6, -1, -1)):
                p_ = cen(c_, r)
                if route:
                    total += abs(p_[0] - route[-1][0]) + abs(p_[1] - route[-1][1])
                route.append(p_); dist[(c_, r)] = total
        by = gy + 7 * step + 9
        if route[-1][1] > gy + 3 * step:
            back = [(route[-1][0], by), (route[0][0] - step, by), (route[0][0] - step, route[0][1]), route[0]]
        else:
            back = [(route[-1][0] + step, route[-1][1]), (route[-1][0] + step, by), (route[0][0] - step, by), (route[0][0] - step, route[0][1]), route[0]]
        pts = route + back
        P = total + sum(abs(pts[i][0] - pts[i - 1][0]) + abs(pts[i][1] - pts[i - 1][1]) for i in range(len(route), len(pts)))
        Dur = 64.0; L = 92.0
        frozen = bool(os.environ.get('STATIC'))
        b = ['<rect x="0.5" y="0.5" width="%d" height="%d" rx="16" fill="%s" stroke="%s"/>' % (W - 1, H - 1, t['panel'], t['line'])]
        last_m = None
        for c_ in range(cols):
            m = int(days[max(0, min(len(days) - 1, c_ * 7 - off))]['date'][5:7])
            if m != last_m and 0 < c_ < cols - 2:
                b.append('<text class="m" x="%.1f" y="24" font-size="9.5" fill="%s">%s</text>' % (gx + c_ * step, t['mute'], MONTHS[m - 1].lower()))
            last_m = m
        eaten = 0
        for i, x in enumerate(days):
            c_, r = (i + off) // 7, (i + off) % 7
            px, py = gx + c_ * step, gy + r * step
            b.append('<rect x="%.1f" y="%.1f" width="%d" height="%d" rx="3" fill="%s"/>' % (px, py, cell, cell, pal[lev(x['n'])]))
            if x['n']:
                eaten += x['n']
                # the cover that hides an eaten cell runs on the same SMIL clock as the snake, so they can never drift apart
                b.append('<rect x="%.1f" y="%.1f" width="%d" height="%d" rx="3" fill="%s" opacity="0">%s</rect>'
                         % (px - 0.5, py - 0.5, cell + 1, cell + 1, pal[0], '' if frozen else
                            '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.46;0.54;1" dur="%ds" begin="%.2fs" repeatCount="indefinite"/>'
                            % (Dur, dist[(c_, r)] / P * Dur - Dur)))
        path = 'M' + ' L'.join('%.1f %.1f' % p_ for p_ in pts) + ' Z'
        b.append('<path id="route" d="%s" fill="none" stroke="none"/>' % path)
        b.append('<path d="%s" fill="none" stroke="%s" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="%.1f %.1f" stroke-dashoffset="%.1f">'
                 '<animate attributeName="stroke-dashoffset" from="%.1f" to="%.1f" dur="%ds" repeatCount="indefinite"/></path>' % (path, t['core'], L, P - L, L, L, L - P, Dur))
        b.append('<path d="%s" fill="none" stroke="%s" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="%.1f %.1f" stroke-dashoffset="%.1f" opacity=".55">'
                 '<animate attributeName="stroke-dashoffset" from="%.1f" to="%.1f" dur="%ds" repeatCount="indefinite"/></path>'
                 % (path, t['glow'] if k == 'dark' else '#8FD0E8', L - 14, P - L + 14, L - 7, L - 7, L - 7 - P, Dur))
        eye = t['night'] if k == 'dark' else '#FFFFFF'
        b.append('<g><circle r="7" fill="%s"/><circle cx="2.4" cy="-2.6" r="1.5" fill="%s"/><circle cx="2.4" cy="2.6" r="1.5" fill="%s"/>'
                 '<animateMotion dur="%ds" repeatCount="indefinite" rotate="auto"><mpath href="#route"/></animateMotion></g>' % (t['hi'], eye, eye, Dur))
        b.append('<text class="m" x="%.1f" y="%.1f" font-size="10.8" fill="%s">one lap = %d contributions eaten, then they grow back</text>' % (gx, H - 14, t['soft'], eaten))
        b.append('<text class="m" x="%.1f" y="%.1f" font-size="10.8" fill="%s" text-anchor="end">less</text>' % (W - gx - 5 * 15 - 38, H - 14, t['mute']))
        b.append('<text class="m" x="%.1f" y="%.1f" font-size="10.8" fill="%s" text-anchor="end">more</text>' % (W - gx, H - 14, t['mute']))
        for i in range(5):
            b.append('<rect x="%.1f" y="%.1f" width="11" height="11" rx="3" fill="%s"/>' % (W - gx - 5 * 15 - 30 + i * 15, H - 24, pal[i]))
        return svg(W, int(H), ''.join(b), 'A snake that eats my contribution graph of the last year')
    return draw


def build(refresh=True):
    c = cfg()
    d = D.load(refresh)
    f = facts(d, c)
    both('room', room(d, f))
    both('mountains', mountains(d, f))
    both('numbers', numbers(d, f))
    both('snake', snake(d, f))
    feat = featured(d)
    for i, r in enumerate(feat):
        both('card-%d' % (i + 1), card(r))
    return d, f, feat
