"""Builds the whole profile: every image in assets/ and README.md. Standard library only, so it runs as is in GitHub Actions.
usage: python scripts/build.py [offline]     offline = draw from scripts/data.json instead of asking the GitHub API
STATIC=1 in the environment freezes all animation at its end state (used for previews)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import static_parts, live_parts, readme

static_parts.build()
d, f, feat = live_parts.build(refresh='offline' not in sys.argv[1:])
readme.write(d, f, feat)
print('built: %d repositories, %d contributions, phase %s, sky %s' % (len(d['repos']), d['total'], f['phase'], f['sky']))
