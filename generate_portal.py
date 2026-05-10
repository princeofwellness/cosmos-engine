#!/usr/bin/env python3
"""
POLARIS Portal — Single-page synthesis HTML generator.
Combines Astrology, Human Design, Numerology, and Chinese Zodiac.

Usage:
    python generate_portal.py "Name" "1997-02-19T10:09:00+00:00" 48.1486 17.1077
    Output: polaris_Name.html
"""

import sys, json, os
from datetime import datetime, timezone

# Add cosmos-engine to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from cosmos.synthesis import SynthesisProfile
from cosmos.constants import SIGNS, PLANETS, ELEMENTS, ASPECTS


def _sign_name(lon: float) -> str:
    s = SIGNS[int(lon / 30) + 1] if int(lon / 30) + 1 <= 12 else SIGNS[12]
    return s["name"]


def _sign_deg_min(lon: float) -> str:
    d = int(lon % 30)
    m = int((lon % 30 - d) * 60)
    return f"{d}°{m:02d}'"


def _aspect_symbol(aspect_name: str) -> str:
    symbols = {
        "conjunction": "☌", "opposition": "☍", "trine": "△", "square": "□",
        "sextile": "⚹", "quincunx": "⚻", "semisextile": "⚺",
        "semisquare": "∠", "sesquiquadrate": "⚼", "quintile": "Q", "biquintile": "bQ",
    }
    return symbols.get(aspect_name, aspect_name)


def generate(profile: SynthesisProfile) -> str:
    """Generate complete POLARIS portal HTML."""
    a = profile.astrology.to_dict()
    n = profile.numerology.to_dict()
    cz = profile.chinese_zodiac.to_dict()

    # === ASTROLOGY EXTRACTS ===
    asc_lon = a["angles"]["ascendant"]
    mc_lon = a["angles"]["midheaven"]
    asc_sign = _sign_name(asc_lon)
    mc_sign = _sign_name(mc_lon)
    asc_pos = _sign_deg_min(asc_lon)
    mc_pos = _sign_deg_min(mc_lon)

    sun = a["planets"]["SUN"]
    moon = a["planets"]["MOON"]
    sun_sign = sun["sign_info"]["sign_name"]
    moon_sign = moon["sign_info"]["sign_name"]

    planet_order = ["SUN","MOON","MERCURY","VENUS","MARS","JUPITER","SATURN","URANUS","NEPTUNE","PLUTO"]
    planet_rows = ""
    for pn in planet_order:
        p = a["planets"].get(pn, {})
        si = p.get("sign_info", {})
        sd = int(si.get("degree", 0))
        sm = int((si.get("degree", 0) - sd) * 60)
        h = p.get("house", "?")
        planet_rows += f"""<tr><td class="planet-name">{pn}</td><td>{si.get('sign_name','')} {sd}°{sm:02d}'</td><td>House {h}</td></tr>"""

    house_rows = ""
    for h in range(1, 13):
        lon = a["houses"]["cusps"].get(str(h), 0)
        sn = _sign_name(lon)
        sd = int(lon % 30)
        sm = int((lon % 30 - sd) * 60)
        label = ""
        if h == 1: label = " ASC"
        elif h == 4: label = " IC"
        elif h == 7: label = " DSC"
        elif h == 10: label = " MC"
        house_rows += f"""<tr><td>House {h}{label}</td><td>{sn} {sd}°{sm:02d}'</td></tr>"""

    aspect_rows = ""
    for aspect in a.get("aspects", [])[:12]:
        sym = _aspect_symbol(aspect["aspect"])
        aspect_rows += f"""<div class="aspect-line"><span class="asp-sym">{sym}</span> {aspect['planet1']} — {aspect['planet2']} <span class="asp-orb">{aspect['deviation']:.2f}°</span></div>"""

    hd_gates_list = ""
    for pn in planet_order + ["CHIRON","NORTH_NODE","SOUTH_NODE"]:
        g = a.get("hd_gates", {}).get(pn, {})
        if g:
            hd_gates_list += f"""<div class="gate-chip"><span class="gate-num">Gate {g['gate']}</span><span class="gate-line">.{g['line']}</span><span class="gate-planet">{pn}</span></div>"""

    elements_html = " ".join(f"""<span class="elem-{e.lower()}">{e}: {a['elements'][e]}</span>""" for e in ELEMENTS)

    # === NUMEROLOGY EXTRACTS ===
    nc = n["core"]
    num_core = f"""
    <div class="num-card"><div class="num-label">Life Path</div><div class="num-value">{nc['life_path']['number']}</div><div class="num-desc">{nc['life_path']['meaning'][:80]}...</div></div>
    <div class="num-card"><div class="num-label">Destiny</div><div class="num-value">{nc['destiny']['number']}</div><div class="num-desc">{nc['destiny']['meaning'][:80]}...</div></div>
    <div class="num-card"><div class="num-label">Soul Urge</div><div class="num-value">{nc['soul_urge']['number']}</div><div class="num-desc">{nc['soul_urge']['meaning'][:80]}...</div></div>
    <div class="num-card"><div class="num-label">Personality</div><div class="num-value">{nc['personality']['number']}</div><div class="num-desc">{nc['personality']['meaning'][:80]}...</div></div>
    <div class="num-card"><div class="num-label">Maturity</div><div class="num-value">{nc['maturity']['number']}</div><div class="num-desc">{nc['maturity']['meaning'][:80]}...</div></div>
    """

    # === CHINESE ZODIAC EXTRACTS ===
    animal = cz["animal"]
    pillars = cz["four_pillars"]
    cz_info = f"""
    <div class="cz-animal">{animal['chinese']} {animal['name']}</div>
    <div class="cz-element-tag">{animal['element']}</div>
    <div class="cz-traits">{animal['traits'][:120]}</div>
    """
    pillar_rows = ""
    for pname, pdata in pillars.items():
        pillar_rows += f"""<div class="pillar"><span class="pillar-label">{pname.upper()}</span> <span>{pdata['stem']}{pdata['branch']}</span> <span class="pillar-elem">({pdata['stem_element']}/{pdata['branch_element']})</span></div>"""

    day_master = cz["day_master"]
    element_bal = cz["element_balance"]
    elem_bal_html = " ".join(f"""<span class="elem-count">{e}: {element_bal['counts'][e]}</span>""" for e in element_bal["counts"])

    # === BUILD HTML ===
    name_safe = profile.name.replace(" ", "_")
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>POLARIS — {profile.name}</title>
<style>
:root {{
  --void: #050812; --stone: #0a0e1a; --tablet: rgba(255,252,235,0.04);
  --gold: #D4A85A; --amber: #C4924A; --ink: rgba(250,245,230,0.93);
  --ink-muted: rgba(240,230,210,0.48); --hairline: rgba(255,255,240,0.06);
  --astro: #D4A85A; --hd: #9b96ff; --num: #589bc8; --cz: #c37341;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  background: var(--void); color: var(--ink);
  font-family: Georgia, 'Times New Roman', serif;
  line-height: 1.7; font-size: 15px;
  -webkit-font-smoothing: antialiased;
}}
.container {{ max-width: 780px; margin:0 auto; padding: 60px 24px 100px; }}

.header {{ text-align:center; margin-bottom: 56px; padding-bottom: 40px; border-bottom: 1px solid var(--hairline); }}
.header .sigil {{ font-size: 40px; color: var(--gold); letter-spacing: 6px; margin-bottom: 12px; }}
.header h1 {{ font-size: 20px; font-weight: 300; color: var(--ink); letter-spacing: 3px; margin-bottom: 6px; }}
.header .sub {{ font-size: 12px; color: var(--ink-muted); letter-spacing: 2px; }}

.system-section {{ margin-bottom: 52px; }}
.system-section h2 {{
  font-size: 13px; font-weight: 400; letter-spacing: 3px; text-transform: uppercase;
  padding-bottom: 8px; border-bottom: 1px solid var(--hairline); margin-bottom: 24px;
}}
h2.astro {{ color: var(--astro); }} h2.hd {{ color: var(--hd); }}
h2.num {{ color: var(--num); }} h2.cz {{ color: var(--cz); }}

.card {{
  padding: 18px 22px; margin: 14px 0;
  border: 1px solid var(--hairline); background: var(--stone);
  border-radius: 2px;
}}
.card-label {{ font-size: 10px; text-transform: uppercase; letter-spacing: 2px; color: var(--gold); margin-bottom: 8px; }}

table {{ width:100%; border-collapse:collapse; font-size:13px; }}
td {{ padding: 5px 10px; border-bottom: 1px solid var(--hairline); }}
td:first-child {{ color: var(--ink-muted); }}
.planet-name {{ color: var(--gold); font-weight: 500; }}

.aspect-line {{ font-size:12px; padding:3px 0; color: var(--ink-muted); }}
.asp-sym {{ color: var(--gold); margin-right:6px; }}
.asp-orb {{ color: var(--ink-muted); font-size:11px; }}

.gate-chip {{
  display: inline-block; padding: 4px 10px; margin: 3px;
  border: 1px solid var(--hairline); font-size: 11px;
  font-family: 'SF Mono', 'Menlo', monospace;
}}
.gate-num {{ color: var(--hd); }} .gate-line {{ color: var(--ink-muted); }} .gate-planet {{ color: var(--ink-muted); font-size:9px; margin-left:6px; }}

.num-card {{
  display: inline-block; width: 130px; padding: 14px; margin: 6px;
  border: 1px solid var(--hairline); text-align: center; vertical-align: top;
}}
.num-value {{ font-size: 36px; font-weight: 300; color: var(--num); }}
.num-label {{ font-size: 9px; text-transform: uppercase; letter-spacing: 2px; color: var(--ink-muted); margin-bottom: 4px; }}
.num-desc {{ font-size: 10px; color: var(--ink-muted); margin-top: 6px; line-height: 1.4; }}

.cz-animal {{ font-size: 28px; color: var(--cz); font-weight: 300; }}
.cz-element-tag {{ display:inline-block; padding:3px 10px; border:1px solid var(--hairline); font-size:11px; color: var(--cz); margin:6px 0; }}
.cz-traits {{ font-size:12px; color: var(--ink-muted); margin-top:6px; }}

.pillar {{ font-size:12px; padding:4px 0; color: var(--ink-muted); }}
.pillar-label {{ color: var(--cz); font-weight:500; font-size:10px; letter-spacing:1px; }}
.pillar-elem {{ font-size:10px; }}

.elem-count {{ font-size:11px; margin-right:10px; color: var(--ink-muted); }}
.elem-fire {{ color: #c94f3a; }} .elem-earth {{ color: #8b9a6b; }} .elem-air {{ color: #5b9bd5; }} .elem-water {{ color: #588bb8; }}

.footnote {{
  margin-top:72px; padding-top:24px; border-top:1px solid var(--hairline);
  font-size:10px; color:rgba(240,230,210,0.18); text-align:center; line-height:1.8;
}}
</style>
</head>
<body>
<div class="container">

<header class="header">
  <div class="sigil">✧</div>
  <h1>{profile.name}</h1>
  <div class="sub">{sun_sign} Sun · {moon_sign} Moon · {asc_sign} Rising · {animal['name']} Spirit</div>
</header>

<!-- ASTROLOGY -->
<section class="system-section">
  <h2 class="astro">✦ Astrology</h2>
  <div class="card">
    <div class="card-label">Planetary Positions</div>
    <table>{planet_rows}</table>
  </div>
  <div class="card">
    <div class="card-label">House Cusps (Placidus)</div>
    <table>{house_rows}</table>
  </div>
  <div class="card">
    <div class="card-label">Elements</div>
    <p style="font-size:13px;">{elements_html}</p>
    <p style="font-size:12px; color:var(--ink-muted); margin-top:8px;">Dominant: <strong style="color:var(--ink);">{a['dominant']['element']}</strong> / {a['dominant']['modality']}</p>
  </div>
  <div class="card">
    <div class="card-label">Key Aspects</div>
    {aspect_rows}
  </div>
</section>

<!-- HUMAN DESIGN -->
<section class="system-section">
  <h2 class="hd">◈ Human Design Gates</h2>
  <div class="card">
    <div class="card-label">Activated Gates (Tropical)</div>
    <div style="line-height:2.2;">{hd_gates_list}</div>
  </div>
</section>

<!-- NUMEROLOGY -->
<section class="system-section">
  <h2 class="num">◉ Numerology</h2>
  <div style="text-align:center;">{num_core}</div>
  <div class="card" style="margin-top:16px;">
    <div class="card-label">Karmic Debts</div>
    <p style="font-size:12px; color:var(--ink-muted);">
      {"None detected" if not n.get('karmic_debts') else 
       ', '.join(f"Karmic Debt {k['number']} ({k['source']})" for k in n['karmic_debts'])}
    </p>
  </div>
</section>

<!-- CHINESE ZODIAC -->
<section class="system-section">
  <h2 class="cz">◎ Chinese Zodiac</h2>
  <div class="card" style="text-align:center;">
    {cz_info}
  </div>
  <div class="card">
    <div class="card-label">Four Pillars of Destiny</div>
    {pillar_rows}
    <p style="font-size:11px; color:var(--ink-muted); margin-top:8px;">
      Day Master: <strong style="color:var(--cz);">{day_master['stem']}</strong> ({day_master['element']} {day_master['polarity']})
    </p>
  </div>
  <div class="card">
    <div class="card-label">Element Balance</div>
    <p style="font-size:13px;">{elem_bal_html}</p>
    <p style="font-size:11px; color:var(--ink-muted); margin-top:8px;">
      Lucky elements: <strong style="color:var(--cz);">{', '.join(element_bal['lucky'])}</strong>
    </p>
  </div>
</section>

<footer class="footnote">
  Generated by POLARIS Portal · Cosmos Engine (MIT) · JPL DE421 ephemerides<br>
  {" · ".join(f"{k}: {v}" for k, v in a.get('elements', {}).items())} · Life Path {nc['life_path']['number']}
</footer>

</div>
</body>
</html>"""
    return html


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python generate_portal.py 'Full Name' '1997-02-19T10:09:00+00:00' 48.1486 17.1077")
        sys.exit(1)

    name = sys.argv[1]
    birth_dt = sys.argv[2]
    lat = float(sys.argv[3])
    lon = float(sys.argv[4])

    print(f"Generating POLARIS portal for {name}...")
    profile = SynthesisProfile(name=name, birth_dt=birth_dt, lat=lat, lon=lon)
    html = generate(profile)

    name_safe = name.replace(" ", "_")
    outpath = f"polaris_{name_safe}.html"
    with open(outpath, "w") as f:
        f.write(html)

    print(f"Saved: {outpath} ({len(html)} bytes)")
