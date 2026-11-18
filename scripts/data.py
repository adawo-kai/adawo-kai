"""Fetches public activity from the GitHub API into scripts/data.json. Token: $GITHUB_TOKEN, or the local `gh` login."""
import datetime, json, os, subprocess, urllib.request
from common import HERE, cfg

QUERY = """query($login:String!){ user(login:$login){ createdAt followers{totalCount}
 contributionsCollection{ totalCommitContributions totalPullRequestContributions totalIssueContributions totalRepositoryContributions
  contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } } }
 repositories(first:100, ownerAffiliations:OWNER, privacy:PUBLIC, orderBy:{field:PUSHED_AT,direction:DESC}){ totalCount
  nodes{ name description url isFork isArchived stargazerCount pushedAt createdAt primaryLanguage{name}
   languages(first:6, orderBy:{field:SIZE,direction:DESC}){ edges{ size node{ name } } } } } } }"""


def token():
    t = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    if t:
        return t
    return subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True, check=True).stdout.strip()


def fetch():
    c = cfg()
    req = urllib.request.Request('https://api.github.com/graphql', data=json.dumps({'query': QUERY, 'variables': {'login': c['login']}}).encode(),
                                 headers={'Authorization': 'bearer ' + token(), 'Content-Type': 'application/json', 'User-Agent': 'profile-readme'})
    u = json.load(urllib.request.urlopen(req, timeout=40))['data']['user']
    cc = u['contributionsCollection']
    days = [{'date': d['date'], 'n': d['contributionCount']} for w in cc['contributionCalendar']['weeks'] for d in w['contributionDays']]
    weeks = [{'start': w['contributionDays'][0]['date'], 'n': sum(d['contributionCount'] for d in w['contributionDays'])} for w in cc['contributionCalendar']['weeks']]
    repos = []
    langs = {}
    for r in u['repositories']['nodes']:
        if r['name'].lower() == c['login'].lower():
            continue
        repos.append({'name': r['name'], 'desc': r['description'] or '', 'url': r['url'], 'fork': r['isFork'], 'stars': r['stargazerCount'],
                      'pushed': r['pushedAt'], 'created': r['createdAt'], 'lang': (r['primaryLanguage'] or {}).get('name') or ''})
        if not r['isFork']:
            for e in r['languages']['edges']:
                langs[e['node']['name']] = langs.get(e['node']['name'], 0) + e['size']
    data = {'fetched': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'), 'login': c['login'], 'since': u['createdAt'][:10],
            'followers': u['followers']['totalCount'], 'total': cc['contributionCalendar']['totalContributions'],
            'commits': cc['totalCommitContributions'], 'prs': cc['totalPullRequestContributions'], 'issues': cc['totalIssueContributions'],
            'new_repos': cc['totalRepositoryContributions'], 'days': days, 'weeks': weeks, 'repos': repos, 'langs': langs}
    json.dump(data, open(os.path.join(HERE, 'data.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    return data


def load(refresh=True):
    p = os.path.join(HERE, 'data.json')
    if refresh:
        try:
            return fetch()
        except Exception as e:                       # offline or rate limited: draw from the last snapshot
            print('fetch failed, using snapshot:', type(e).__name__)
    return json.load(open(p, encoding='utf-8'))
