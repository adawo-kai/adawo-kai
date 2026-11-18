"""Writes README.md (plain HTML that GitHub renders) from the config and the live data."""
import os
from common import *

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def pic(name, alt, attrs='width="100%"'):
    return ('<picture><source media="(prefers-color-scheme: dark)" srcset="assets/%s-dark.svg"><img src="assets/%s-light.svg" alt="%s" %s></picture>'
            % (name, name, esc(alt), attrs))


def write(d, f, feat):
    c = cfg()
    sec = {s['id']: s for s in c['sections']}
    head = lambda i: pic('h-' + i, '%s: %s' % (sec[i]['num'], sec[i]['title']))
    o = []
    o.append('<a href="https://github.com/%s">%s</a>' % (c['login'], pic('hero', '%s, %s. A portrait typed out of characters.' % (c['name'].title(), c['role'].lower()))))
    o.append('<p align="center">\n' + '\n'.join('  <a href="%s" title="%s">%s</a>' % (ln['url'], esc(ln['sub']), pic('btn-' + ln['id'], ln['label'] + ': ' + ln['sub'], 'height="60"'))
                                                 for ln in c['links']) + '\n</p>')
    o.append('<p align="center">%s</p>' % esc(c['intro']))

    o.append(head('room'))
    o.append(pic('room', 'My room right now: the window shows my local time of day, the clouds depend on how much I committed this week, '
                 'the monitor shows my last push, the books are my languages.'))
    o.append('<details>\n<summary><b>How does the room work?</b></summary>\n<br>\n\n'
             '- <b>The window</b> is my local time (UTC%+d): dawn, day, dusk or night with a moon and stars.\n'
             '- <b>The weather is my commits.</b> No contributions for a week and the sky is overcast; ten or more and it is clear. A commit today sends a shooting star across the night sky.\n'
             '- <b>The monitor</b> shows the repository I pushed to last. Two quiet weeks and it falls asleep.\n'
             '- <b>The books</b> are my languages, each as tall as its share of my public code. <b>The plant</b> grows a leaf for every dozen contributions.\n'
             '- <b>The clock and the calendar</b> show the minute the picture was drawn.\n'
             '- No server and no trackers: <a href="scripts/live_parts.py"><code>scripts/live_parts.py</code></a> draws plain SVG from the public GitHub API, '
             'and <a href="scripts/build.py"><code>scripts/build.py</code></a> redraws everything in one run.\n\n</details>' % c['utc_offset_hours'])

    o.append(head('mountains'))
    o.append(pic('mountains', 'My last year of contributions as a mountain range: %d contributions, best week %d. Every repository of mine is a tree.' % (d['total'], f['best']['n'])))

    o.append(head('stack'))
    o.append(pic('stack', 'Stack: ' + '; '.join('%s: %s' % (g['group'], ', '.join(n for n, _ in g['items'])) for g in c['stack'])))

    o.append(head('work'))
    o.append(pic('numbers', '%d public repositories, %d contributions in the last year' % (len(d['repos']), d['total'])))
    cards = ['<a href="%s" title="%s">%s</a>' % (r['url'], esc(r['name']), pic('card-%d' % (i + 1), '%s: %s' % (r['name'], r['desc']), 'width="49.5%"')) for i, r in enumerate(feat)]
    for i in range(0, len(cards), 2):            # two cards per row, a paragraph per row so the rows keep a gap
        o.append('<p align="center">\n  ' + '\n  '.join(cards[i:i + 2]) + '\n</p>')
    rows = []
    for r in d['repos']:
        rows.append('<tr><td><a href="%s" title="%s"><b>%s</b></a>%s</td><td>%s</td><td>%s&nbsp;%s</td></tr>'
                    % (r['url'], esc(r['desc']), esc(r['name']), ' <sub>fork</sub>' if r['fork'] else '', esc(r['lang']), MONTHS[int(r['pushed'][5:7]) - 1], r['pushed'][:4]))
    o.append('<details>\n<summary><b>All %d public repositories</b></summary>\n<br>\n\n<table>\n<tr><th align="left">repository</th><th align="left">language</th>'
             '<th align="left">last push</th></tr>\n%s\n</table>\n\n</details>' % (len(d['repos']), '\n'.join(rows)))

    o.append(head('snake'))
    o.append(pic('snake', 'A snake eating my contribution graph of the last year'))
    o.append(pic('footer', ''))
    text = '\n\n'.join(o) + '\n'
    with open(os.path.join(ROOT, 'README.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    return text
