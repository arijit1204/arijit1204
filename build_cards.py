"""Redraws the profile cards (the .svg files next to this script) from live GitHub data.
Run by .github/workflows/cards.yml. Needs GITHUB_TOKEN in the environment."""
import base64, json, os, sys, textwrap, urllib.request, datetime as dt
from html import escape

USER = "arijit1204"
OUT = os.path.dirname(os.path.abspath(__file__))

# Edit these to change what the cards say.
PROJECTS = [
    ("ScribeBot", "LLM APP",
     "Turns a long YouTube video into a knowledge base you can ask questions. It pulls the transcript, writes a summary, and answers questions about the video.",
     ["LangChain", "Groq", "ChromaDB", "FastAPI"]),
    ("Pixie", "VOICE AGENT",
     "A voice assistant you talk to, running on Gemini 2.0 Flash. You speak, it thinks, and it answers out loud.",
     ["Python", "Gemini", "Speech"]),
    ("dhartisense", "APPLIED AI",
     "Free advice for small farmers. You map your field and it suggests crops, irrigation dates and a fertiliser plan, plus crop health from satellite data.",
     ["Python", "JavaScript", "Satellite"]),
    ("autoeda", "PYTHON LIBRARY",
     "Automated EDA for pandas DataFrames: quality scores, column health checks, plain-language insights and train/test drift detection.",
     ["Python", "pandas", "Data quality"]),
]
PROFILE = {
    "role": "AI engineer",
    "line": "I build LLM apps: RAG pipelines, voice agents and their backends.",
    "place": "Kolkata, India",
    "chips": ["LLM apps", "RAG", "Voice agents", "Applied ML"],
}
NOW_BUILDING = {
    "title": "Indoor navigation for our college fest",
    "line": "It runs on visitors' phones with no beacons or extra hardware.",
    "progress": 0.35,  # 0 to 1
}

# ---------- GitHub data ----------
TOKEN = os.environ.get("GITHUB_TOKEN", "")
def gh(url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": f"bearer {TOKEN}", "User-Agent": USER,
                                          "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def contributions():
    q = """query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{
           weeks{contributionDays{date contributionCount}}}}}}"""
    d = gh("https://api.github.com/graphql", {"query": q, "variables": {"u": USER}})
    days = [x for w in d["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
            for x in w["contributionDays"]]
    return {dt.date.fromisoformat(x["date"]): x["contributionCount"] for x in days}

def user_info():
    u = gh(f"https://api.github.com/users/{USER}")
    repos = gh(f"https://api.github.com/users/{USER}/repos?per_page=100")
    own = [r for r in repos if not r["fork"] and r["name"].lower() != USER.lower()]
    with urllib.request.urlopen(u["avatar_url"] + "&s=200", timeout=30) as r:
        avatar = "data:image/png;base64," + base64.b64encode(r.read()).decode()
    return {"name": u["name"] or USER, "repos": len(own),
            "stars": sum(r["stargazers_count"] for r in own),
            "languages": len({r["language"] for r in own if r["language"]}), "avatar": avatar}

def repo(name):
    return gh(f"https://api.github.com/repos/{USER}/{name}")

# ---------- drawing ----------
CREAM, BLUE, INK, MUTED, BODY = "#f1eadb", "#3178c6", "#1f2328", "#6b6459", "#3d3830"
MONO = 'ui-monospace,SFMono-Regular,Menlo,Consolas,&quot;Liberation Mono&quot;,monospace'
SANS = '-apple-system,&quot;Segoe UI&quot;,Inter,Helvetica,Arial,sans-serif'

def shell(W, H, title, right=""):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
            f'<clipPath id="cl"><rect width="{W}" height="{H}" rx="14"/></clipPath><g clip-path="url(#cl)">',
            f'<rect width="{W}" height="{H}" fill="{CREAM}"/><rect width="{W}" height="34" fill="{BLUE}"/>',
            f'<text x="26" y="22" fill="{CREAM}" font-family="{MONO}" font-size="12" font-weight="700" letter-spacing="1.6">{escape(title)}</text>',
            f'<text x="{W-26}" y="22" fill="{CREAM}" fill-opacity="0.75" font-family="{MONO}" font-size="11" letter-spacing="1.2" text-anchor="end">{escape(right)}</text>']

def save(name, o):
    o.append("</g></svg>")
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write("\n".join(o))

def stat(x, y, label, val, b):
    return (f'<g opacity="0"><animate attributeName="opacity" to="1" begin="{b}s" dur="0.5s" fill="freeze"/>'
            f'<text x="{x}" y="{y}" fill="{MUTED}" font-family="{MONO}" font-size="11" letter-spacing="1.6">{label}</text>'
            f'<text x="{x}" y="{y+28}" fill="{INK}" font-family="{SANS}" font-size="23" font-weight="800">{val}</text></g>')

def grow(y_base, h, b):
    s = 'calcMode="spline" keyTimes="0;1" keySplines="0.2 0.9 0.2 1"'
    return (f'<animate attributeName="height" to="{h:.0f}" begin="{b:.2f}s" dur="0.6s" fill="freeze" {s}/>'
            f'<animate attributeName="y" to="{y_base-h:.0f}" begin="{b:.2f}s" dur="0.6s" fill="freeze" {s}/>')

def commits_card(c, today):
    weeks = []
    for i in range(25, -1, -1):
        end = today - dt.timedelta(days=7 * i); start = end - dt.timedelta(days=6)
        weeks.append((start, sum(v for d, v in c.items() if start <= d <= end)))
    active = sorted(d for d, v in c.items() if v)
    best = run = 0; prev = None
    for d in active:
        run = run + 1 if prev and (d - prev).days == 1 else 1
        best = max(best, run); prev = d
    streak = 0; d = today if c.get(today) else today - dt.timedelta(days=1)
    while c.get(d): streak += 1; d -= dt.timedelta(days=1)
    year_total = sum(v for d, v in c.items() if d.year == today.year)
    busiest = max(weeks, key=lambda w: w[1])

    W, H = 880, 250
    o = shell(W, H, "EQUALIZER · 26 WEEKS OF COMMITS",
              f"{weeks[0][0]:%b} → {today:%b %Y}".upper())
    bx, base, bw, maxh = 36, 206, 17, 140; gap = (500 - bx) / 26
    mx = max(1, busiest[1]); shades = ["#a9c5e8", "#78a3d8", BLUE, "#245a99"]
    for i, (s, v) in enumerate(weeks):
        x = bx + i * gap
        if v == 0:
            o.append(f'<rect x="{x:.1f}" y="{base-3}" width="{bw}" height="3" rx="1.5" fill="#d8cdb8"/>'); continue
        h = max(8, v / mx * maxh)
        o.append(f'<rect x="{x:.1f}" y="{base}" width="{bw}" height="0" rx="3" fill="{shades[min(3, int(v/mx*4))]}">'
                 f'<title>week of {s:%d %b}: {v}</title>{grow(base, h, 0.2 + i*0.05)}</rect>')
    last = -9
    for i, (s, _) in enumerate(weeks):  # month labels at the first week of each month
        if i == 0 or s.month != weeks[i-1][0].month:
            if i <= 23 and i - last >= 3:
                last = i
                o.append(f'<text x="{bx+i*gap:.0f}" y="{base+20}" fill="{MUTED}" font-family="{MONO}" font-size="10" letter-spacing="1">' + f"{s:%b}".upper() + '</text>')
    sx = 575
    o.append(stat(sx, 74, "CURRENT STREAK", f"{streak} day" + ("" if streak == 1 else "s"), 1.4))
    o.append(stat(sx + 160, 74, "LONGEST RUN", f"{best} days", 1.6))
    o.append(stat(sx, 150, "BUSIEST WEEK", f"{busiest[1]}", 1.8))
    o.append(stat(sx + 160, 150, f"IN {today.year}", f"{year_total}", 2.0))
    o.append(f'<text x="{sx}" y="226" fill="{MUTED}" font-family="{MONO}" font-size="10" letter-spacing="1">UPDATED ' + f"{today:%d %b}".upper() + '</text>')
    save("commits.svg", o)

def project_card(i, name, kind, desc, tags, info):
    W, H = 440, 236
    pushed = dt.date.fromisoformat(info["pushed_at"][:10]) if info else None
    right = f"UPDATED {pushed:%d %b}".upper() if pushed else "REPO ↗"
    o = shell(W, H, f"{i:02d} · {kind}", right)
    o.append(f'<text x="26" y="78" fill="{INK}" font-family="{SANS}" font-size="26" font-weight="800">{escape(name)}</text>')
    if info and info.get("stargazers_count"):
        o.append(f'<text x="{W-26}" y="76" fill="{BLUE}" font-family="{MONO}" font-size="13" text-anchor="end">★ {info["stargazers_count"]}</text>')
    for k, line in enumerate(textwrap.wrap(desc or (info or {}).get("description") or "", 55)[:4]):
        o.append(f'<text x="26" y="{108+k*20}" fill="{BODY}" font-family="{SANS}" font-size="13.5">{escape(line)}</text>')
    x = 26
    for t in tags:
        w = len(t) * 7.2 + 20
        o.append(f'<rect x="{x:.0f}" y="190" width="{w:.0f}" height="24" rx="12" fill="none" stroke="{BLUE}" stroke-width="1.3"/>'
                 f'<text x="{x+w/2:.0f}" y="206" fill="{BLUE}" font-family="{MONO}" font-size="11.5" text-anchor="middle">{escape(t)}</text>')
        x += w + 8
    save(f"project-{name.lower()}.svg", o)

def profile_card(info, year_total, today):
    W, H = 880, 230
    o = shell(W, H, f"PROFILE · @{USER}".upper(), PROFILE["place"].upper())
    cx, cy, r = 100, 132, 58
    o.append(f'<clipPath id="av"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{r+5}" fill="none" stroke="{BLUE}" stroke-width="3"/>')
    if info.get("avatar"):
        o.append(f'<image href="{info["avatar"]}" x="{cx-r}" y="{cy-r}" width="{2*r}" height="{2*r}" clip-path="url(#av)" preserveAspectRatio="xMidYMid slice"/>')
    else:
        o.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#ddd2bd"/>')
    x = 190
    o.append(f'<text x="{x}" y="92" fill="{MUTED}" font-family="{MONO}" font-size="12" letter-spacing="1.6">{escape(PROFILE["role"].upper())}</text>')
    o.append(f'<text x="{x}" y="130" fill="{INK}" font-family="{SANS}" font-size="36" font-weight="800">{escape(info["name"])}</text>')
    o.append(f'<text x="{x}" y="156" fill="{BODY}" font-family="{SANS}" font-size="13.5">{escape(PROFILE["line"])}</text>')
    for t in PROFILE["chips"]:
        w = len(t) * 7.2 + 22
        o.append(f'<rect x="{x:.0f}" y="174" width="{w:.0f}" height="26" rx="13" fill="{BLUE}"/>'
                 f'<text x="{x+w/2:.0f}" y="191" fill="{CREAM}" font-family="{MONO}" font-size="11.5" text-anchor="middle">{escape(t)}</text>')
        x += w + 8
    o.append(f'<line x1="690" y1="62" x2="690" y2="204" stroke="#ddd2bd"/>')
    o.append(stat(712, 78, "REPOS", f"{info['repos']}", 0.3))
    o.append(stat(800, 78, "STARS", f"{info['stars']}", 0.45))
    o.append(stat(712, 150, f"IN {today.year}", f"{year_total}", 0.6))
    o.append(stat(800, 150, "LANGS", f"{info['languages']}", 0.75))
    save("profile.svg", o)

def now_card(today):
    W, H = 880, 150; p = max(0, min(1, NOW_BUILDING["progress"]))
    o = shell(W, H, "NOW BUILDING", f"{int(p*100)}% · {today:%d %b}".upper())
    o.append(f'<text x="26" y="80" fill="{INK}" font-family="{SANS}" font-size="24" font-weight="800">{escape(NOW_BUILDING["title"])}</text>')
    o.append(f'<text x="26" y="106" fill="{BODY}" font-family="{SANS}" font-size="13.5">{escape(NOW_BUILDING["line"])}</text>')
    o.append(f'<rect x="26" y="122" width="828" height="8" rx="4" fill="#ddd2bd"/>')
    o.append(f'<rect x="26" y="122" width="0" height="8" rx="4" fill="{BLUE}"><animate attributeName="width" to="{828*p:.0f}" begin="0.4s" dur="1.6s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.2 0.9 0.2 1"/></rect>')
    o.append(f'<circle cx="{26+828*p:.0f}" cy="126" r="7" fill="{BLUE}" opacity="0"><set attributeName="opacity" to="1" begin="2s" fill="freeze"/><animate attributeName="r" values="5;8;5" dur="1.4s" begin="2s" repeatCount="indefinite"/></circle>')
    save("now-building.svg", o)

def main(fixture=None):
    os.makedirs(OUT, exist_ok=True)
    today = dt.date.today()
    if fixture:  # offline test: python build_cards.py fixture.json
        f = json.load(open(fixture)); today = dt.date.fromisoformat(f["today"])
        c = {dt.date.fromisoformat(k): v for k, v in f["days"].items()}; repos = f["repos"]; info = f.get("info")
    else:
        c = contributions(); repos = {}
        try: info = user_info()
        except Exception as e: print("profile lookup failed:", e); info = None
        for name, *_ in PROJECTS:
            try: repos[name] = repo(name)
            except Exception as e: print("repo lookup failed:", name, e); repos[name] = None
    commits_card(c, today)
    for i, (name, kind, desc, tags) in enumerate(PROJECTS, 1):
        project_card(i, name, kind, desc, tags, repos.get(name))
    now_card(today)
    if info:
        profile_card(info, sum(v for d, v in c.items() if d.year == today.year), today)
    print("cards written to", os.path.abspath(OUT))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
