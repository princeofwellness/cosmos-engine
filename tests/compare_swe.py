#!/usr/bin/env python3
"""Compare cosmos-engine vs Swiss Ephemeris for accuracy verification."""

import sys
sys.path.insert(0, '/tmp/hd-research')

from cosmos.chart import Chart
from datetime import datetime, timezone
import swisseph as swe

# Test date: Feb 19, 1997 10:09 UTC, Bratislava
dt = datetime(1997, 2, 19, 10, 9, 0, tzinfo=timezone.utc)
lat, lon = 48.1486, 17.1077

print("=" * 70)
print("COSMOS ENGINE vs SWISS EPHEMERIS — ACCURACY COMPARISON")
print("=" * 70)
print(f"Birth: {dt.isoformat()}")
print(f"Location: {lat}, {lon}")
print()

# Cosmos engine
chart = Chart(dt, lat, lon, house_system="P")
cosmos = chart.to_dict()

# Swiss Ephemeris
jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0 + dt.second / 3600.0)
swe.set_sid_mode(0)

# Planet positions
planet_ids = {
    "SUN": swe.SUN, "MOON": swe.MOON, "MERCURY": swe.MERCURY,
    "VENUS": swe.VENUS, "MARS": swe.MARS, "JUPITER": swe.JUPITER,
    "SATURN": swe.SATURN, "URANUS": swe.URANUS, "NEPTUNE": swe.NEPTUNE,
    "PLUTO": swe.PLUTO,
}

# True node
swe_node_result = swe.calc_ut(jd, swe.TRUE_NODE)
node_lon = swe_node_result[0] if not isinstance(swe_node_result[0], tuple) else swe_node_result[0][0]

print("=== PLANETARY LONGITUDES ===")
print(f"{'Planet':14s} {'Cosmos':>10s} {'SwissEph':>10s} {'Diff':>8s} {'Status'}")
print("-" * 60)

max_diff = 0.0
max_planet = ""
for name, pid in planet_ids.items():
    c_lon = cosmos["planets"][name]["longitude"]
    result = swe.calc_ut(jd, pid)
    s_lon = result[0] if not isinstance(result[0], tuple) else result[0][0]
    diff = c_lon - s_lon
    if abs(diff) > abs(max_diff):
        max_diff = diff
        max_planet = name
    status = "✓" if abs(diff) < 0.1 else ("⚠" if abs(diff) < 1.0 else "✗")
    print(f"{name:14s} {c_lon:10.4f}° {s_lon:10.4f}° {diff:+8.4f}° {status}")

# North Node
c_node = cosmos["planets"]["NORTH_NODE"]["longitude"]
n_diff = c_node - node_lon
if abs(n_diff) > abs(max_diff):
    max_diff = n_diff
    max_planet = "NORTH_NODE"
status = "✓" if abs(n_diff) < 0.5 else ("⚠" if abs(n_diff) < 1.0 else "✗")
print(f"{'NORTH_NODE':14s} {c_node:10.4f}° {node_lon:10.4f}° {n_diff:+8.4f}° {status} (mean node formula)")

print(f"\nMax deviation: {max_planet} = {max_diff:.4f}°")

# House comparison
print(f"\n=== HOUSE CUSPS (PLACIDUS) ===")
swe_houses = swe.houses(jd, lat, lon, b'P')
swe_asc = swe_houses[0][0]
swe_mc = swe_houses[0][9]
swe_cusps = {i: swe_houses[0][i-1] for i in range(1, 13)}

print(f"{'Angle':14s} {'Cosmos':>10s} {'SwissEph':>10s} {'Diff':>8s} {'Status'}")
print("-" * 60)
c_asc = cosmos["angles"]["ascendant"]
c_mc = cosmos["angles"]["midheaven"]
print(f"{'ASC':14s} {c_asc:10.4f}° {swe_asc:10.4f}° {c_asc - swe_asc:+8.4f}° {'⚠' if abs(c_asc - swe_asc) > 1 else '✓'}")
print(f"{'MC':14s} {c_mc:10.4f}° {swe_mc:10.4f}° {c_mc - swe_mc:+8.4f}° {'⚠' if abs(c_mc - swe_mc) > 1 else '✓'}")

for h in range(1, 13):
    c_cusp = cosmos["houses"]["cusps"][str(h)]
    s_cusp = swe_cusps[h]
    diff = c_cusp - s_cusp
    status = "✓" if abs(diff) < 1.0 else ("⚠" if abs(diff) < 3.0 else "✗")
    print(f"{'House '+str(h):14s} {c_cusp:10.4f}° {s_cusp:10.4f}° {diff:+8.4f}° {status}")

# Aspect comparison
print(f"\n=== ASPECTS ===")
print(f"Cosmos: {len(cosmos['aspects'])} aspects")
print(f"Swiss Eph aspects not compared (use cosmos aspect engine)")

print(f"\n=== HD GATES ===")
for name in ["SUN", "MOON", "MERCURY", "VENUS"]:
    if name in chart.hd_gates:
        g = chart.hd_gates[name]
        print(f"  {name}: Gate {g['gate']}.{g['line']}")

print(f"\n{'='*70}")
print("VERDICT:")
planet_ok = True
for name, pid in planet_ids.items():
    c_lon = cosmos["planets"][name]["longitude"]
    result = swe.calc_ut(jd, pid)
    s_lon = result[0] if not isinstance(result[0], tuple) else result[0][0]
    diff = abs(c_lon - s_lon)
    if diff > 0.1:
        planet_ok = False
        break
if planet_ok:
    print("  Planets: ✓ PASS (< 0.1° for all major bodies)")
else:
    print(f"  Planets: ✗ NEEDS WORK (max diff: {max_diff:.4f}°)")
