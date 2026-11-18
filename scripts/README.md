# How this profile is drawn

Everything on the profile is plain SVG written by the Python in this folder. No third-party widgets, no trackers.

| file | what it does |
|---|---|
| `build.py` | one command that redraws everything: `python scripts/build.py` (`offline` = use the saved `data.json`) |
| `common.py` | the design system: one cerulean palette (`#007BA7`), light and dark themes, SVG helpers, block letters |
| `static_parts.py` | hero with the character portrait, link buttons, section headers, stack panel, footer |
| `live_parts.py` | the room, the commit mountains, the numbers, repository cards, the snake |
| `data.py` | reads public activity from the GitHub API into `data.json` |
| `readme.py` | writes `README.md` |
| `make_portrait.py` | one-off: turns a photo into `portrait.json` (needs Pillow and numpy; the build itself needs only the standard library) |
| `profile.json` | all the text: name, links, sections, stack, featured repositories |
| `icons/` | brand glyphs from [Simple Icons](https://simpleicons.org) (CC0) |

To change the text, the links or the stack, edit `profile.json` and run the build.
`automation/profile.yml` is the GitHub Actions workflow that runs the build every hour; see the note at its top for switching it on.
