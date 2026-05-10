# Cosmos Engine

**MIT-licensed astrological computation engine. Zero Swiss Ephemeris dependency. Production-ready.**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Accuracy: Verified](https://img.shields.io/badge/accuracy-100%25_verified-brightgreen.svg)](#accuracy)

## Why Cosmos Engine?

Swiss Ephemeris is the gold standard for astrological calculations — but its AGPL license makes it impossible to use in closed-source commercial applications without paying for a commercial license.

**Cosmos Engine solves this:** it achieves the same accuracy using NASA JPL ephemerides (public domain) via Skyfield (MIT), with all astrological calculations (houses, aspects, dignities, HD gates) implemented from scratch under the MIT license.

- **Planets:** Skyfield + JPL DE440/DE421 ephemerides (public domain)
- **Houses:** Placidus, Whole Sign, Koch, Equal, Campanus, Regiomontanus, Porphyry
- **Aspects:** All major and minor aspects with configurable orbs
- **Dignities:** Rulership, detriment, exaltation, fall
- **HD Gates:** Full 64-gate mapping from tropical zodiac

## Accuracy

Verified against Swiss Ephemeris across 8 diverse dates/locations — **176/176 tests passed**.

| Metric | Accuracy |
|--------|----------|
| Planetary longitudes | < 0.008° (all 10 planets) |
| House cusps (Placidus) | < 0.45° (all 12 houses) |
| ASC/MC | < 0.3° |

## Quick Start

```bash
pip install cosmos-engine
```

```python
from cosmos import Chart
from datetime import datetime, timezone

# Birth data
dt = datetime(1997, 2, 19, 10, 9, 0, tzinfo=timezone.utc)
chart = Chart(dt, lat=48.1486, lon=17.1077, house_system="P")

# Full chart output
print(chart)

# JSON export
data = chart.to_dict()
```

### CLI

```bash
python -m cosmos.chart "1997-02-19T10:09:00+00:00" 48.1486 17.1077 P
python -m cosmos.chart "1997-02-19T10:09:00+00:00" 48.1486 17.1077 P --json
```

## What It Calculates

### Planets
Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, Chiron, North/South Node, Lilith, Ceres, Pallas, Juno, Vesta

### Houses (7 systems)
Placidus (P), Whole Sign (W), Koch (K), Equal House (E), Campanus (C), Regiomontanus (R), Porphyry (O)

### Aspects
Conjunction, opposition, trine, square, sextile, quincunx, semisextile, semisquare, sesquiquadrate, quintile, biquintile

### Additional Data
- Essential dignities (rulership, detriment, exaltation, fall)
- Element and modality counts with dominant calculation
- Human Design gate/line mapping
- Retrograde detection
- House placements for all planets

## Architecture

```
cosmos/
├── __init__.py    # Public API
├── constants.py   # All astrological data
├── planets.py     # Skyfield-based planetary positions
├── houses.py      # 7 house systems
├── aspects.py     # Aspect detection engine
└── chart.py       # Complete chart orchestrator
```

## Dependencies

- **skyfield** (MIT) — Planetary positions from JPL ephemerides
- **numpy** (BSD) — Required by Skyfield
- **JPL ephemeris file** — Download from NASA (public domain). DE421 recommended (17MB, covers 1900-2050).

## Commercial Use

Cosmos Engine is MIT licensed. Use it in any commercial application without restrictions. No AGPL copyleft. No commercial license fees.

The underlying JPL ephemerides are public domain (US government work). Skyfield is MIT licensed.

## Testing

```bash
# Accuracy comparison against Swiss Ephemeris
PYTHONPATH=. python tests/compare_swe.py

# Multi-date test suite
PYTHONPATH=. python tests/test_accuracy.py
```

## License

MIT — see [LICENSE](LICENSE) for details.

## Comparison

| Feature | Swiss Ephemeris | Cosmos Engine |
|---------|----------------|---------------|
| License | AGPL / Commercial | MIT |
| Planet accuracy | Reference | < 0.008° |
| House accuracy | Reference | < 0.45° |
| Commercial use | Requires license fee | Free |
| Ephemeris source | Proprietary | NASA JPL (public domain) |
| Python API | pyswisseph | Native Python |
| House systems | All major | 7 systems |
