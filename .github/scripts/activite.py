"""Génère visuels/activite-{sombre,clair}.svg à partir de l'API GraphQL de GitHub."""
import json, os, urllib.request
from datetime import date

LOGIN = os.environ.get("LOGIN", "krm3z")
QUERY = """query($login:String!){user(login:$login){
  contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}
  repositories(ownerAffiliations:OWNER,privacy:PUBLIC,first:100,isFork:false){totalCount
    nodes{stargazerCount languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}}}"""

req = urllib.request.Request("https://api.github.com/graphql",
    data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
    headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"})
user = json.load(urllib.request.urlopen(req))["data"]["user"]

cal = user["contributionsCollection"]["contributionCalendar"]
weeks = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in cal["weeks"]][-52:]
repos = user["repositories"]
langs = {}
for r in repos["nodes"]:
    for e in r["languages"]["edges"]:
        langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
total = sum(langs.values()) or 1
top = sorted(langs.items(), key=lambda x: -x[1])[:4]

SANS = "Helvetica, Arial, sans-serif"; SERIF = "Georgia, 'Times New Roman', serif"
THEMES = {"sombre": dict(bg="#1C1B19", line="#3A3631", ink="#EDE6DA", acc="#B89B72", mut="#8C8273", shades=["#B89B72", "#8C7A60", "#5E5446", "#3F3A33"]),
          "clair": dict(bg="#FAF8F4", line="#E2DBCF", ink="#1C1B19", acc="#8A6A3E", mut="#6F665A", shades=["#8A6A3E", "#B39872", "#D2C2A6", "#E8DECD"])}
fr = lambda n: f"{n:,}".replace(",", " ")
t = lambda x, y, s, size, fill, font=SANS, a="start": f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" fill="{fill}" text-anchor="{a}">{s}</text>'

for name, T in THEMES.items():
    W, H = 900, 250
    b = f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="{T["bg"]}" stroke="{T["line"]}"/>'
    kp = [(fr(cal["totalContributions"]), "contributions sur 12 mois"), (str(max(weeks)), "contributions, meilleure semaine"), (str(repos["totalCount"]), "dépôts publics")]
    for i, (n, l) in enumerate(kp):
        b += t(40, 64 + i * 58, n, 30, T["ink"], SERIF) + t(40, 84 + i * 58, l, 12, T["acc"])
    # barres hebdomadaires
    x0, x1, yb, hmax = 260, 860, 170, 120
    m = max(weeks) or 1; bw = (x1 - x0) / len(weeks)
    b += t(x0, 36, "Contributions par semaine", 12, T["mut"])
    for i, v in enumerate(weeks):
        h = max(1.5, v / m * hmax) if v else 1.5
        b += f'<rect x="{x0+i*bw+1:.1f}" y="{yb-h:.1f}" width="{bw-2:.1f}" height="{h:.1f}" rx="1" fill="{T["acc"] if v else T["line"]}"/>'
    b += t(x0, yb + 16, "il y a 12 mois", 10, T["mut"]) + t(x1, yb + 16, "cette semaine", 10, T["mut"], a="end")
    # langages
    x = x0
    for i, (lang, size) in enumerate(top):
        w = (x1 - x0) * size / sum(s for _, s in top)
        b += f'<rect x="{x:.1f}" y="200" width="{max(0,w-2):.1f}" height="8" rx="2" fill="{T["shades"][i]}"/>'
        x += w
    x = x0
    for i, (lang, size) in enumerate(top):
        b += f'<rect x="{x}" y="222" width="8" height="8" rx="2" fill="{T["shades"][i]}"/>' + t(x + 14, 230, f"{lang} {round(100*size/total)} %", 11, T["mut"])
        x += 150
    open(f"visuels/activite-{name}.svg", "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{b}</svg>')
print("ok", cal["totalContributions"], repos["totalCount"], top)
