"""
Complete astrological chart calculation.

Orchestrates planetary positions, house cusps, aspects, and
all derived astrological data into a single rich output.
"""

import math
from datetime import datetime, timezone
from typing import Optional

from .planets import PlanetPositions, PlanetPosition
from .houses import HouseSystem
from .aspects import AspectEngine
from .constants import (
    PLANETS, SIGNS, ASPECTS, ELEMENTS, MODALITIES,
    RULERSHIP, EXALTATION, DETRIMENT, FALL_SIGN,
    GATE_DEGREES, GATE_LINE_DEGREE,
)


class Chart:
    """Complete astrological chart.
    
    Calculates and holds all chart data: planets, houses, aspects,
    dignities, elements, modalities, and Human Design gate data.
    """
    
    def __init__(self, dt: datetime, lat: float, lon: float,
                 house_system: str = "P",
                 ephemeris_path: str = "/tmp/hd-research/de421.bsp",
                 sidereal: bool = False, ayanamsa: float = 0.0):
        """
        Args:
            dt: Birth datetime (must be timezone-aware)
            lat: Geographic latitude (positive=N)
            lon: Geographic longitude (positive=E)
            house_system: P=Placidus, W=Whole Sign, K=Koch, E=Equal, etc.
            ephemeris_path: Path to JPL .bsp ephemeris file
            sidereal: Use sidereal zodiac (default: tropical)
            ayanamsa: Ayanamsa value in degrees (if sidereal=True)
        """
        self.dt = dt
        self.lat = lat
        self.lon = lon
        self.house_system = house_system
        self.sidereal = sidereal
        self.ayanamsa = ayanamsa
        
        # Calculate all components
        self.planets = PlanetPositions(dt, ephemeris_path=ephemeris_path)
        self.houses = HouseSystem(dt, lat, lon, system=house_system, 
                                   planet_positions=self.planets)
        self.aspects = AspectEngine(self.planets.positions)
        
        # Derived data
        self._compute_derived()
    
    def _compute_derived(self):
        """Compute all derived chart data."""
        self.planet_signs = {}
        self.planet_houses = {}
        self.element_counts = {e: 0 for e in ELEMENTS}
        self.modality_counts = {m: 0 for m in MODALITIES}
        self.house_signs = {}
        
        # Planet signs and houses
        for name, pos in self.planets.positions.items():
            lon = pos.lon
            if self.sidereal:
                lon = (lon - self.ayanamsa) % 360.0
            
            sign_num = int(lon / 30) + 1
            if sign_num > 12:
                sign_num = 1
            sign_degree = lon % 30
            
            self.planet_signs[name] = {
                "sign": sign_num,
                "degree": sign_degree,
                "sign_name": SIGNS[sign_num]["name"],
                "sign_symbol": SIGNS[sign_num]["symbol"],
            }
            
            # House placement
            house_num = self.houses.get_house(lon)
            self.planet_houses[name] = house_num
            
            # Element and modality counts (for Sun through Pluto only)
            if name in ["SUN", "MOON", "MERCURY", "VENUS", "MARS", 
                         "JUPITER", "SATURN", "URANUS", "NEPTUNE", "PLUTO"]:
                elem = SIGNS[sign_num]["element"]
                mod = SIGNS[sign_num]["modality"]
                self.element_counts[elem] += 1
                self.modality_counts[mod] += 1
        
        # House sign mapping
        for h in range(1, 13):
            cusp_lon = self.houses.cusps.cusps.get(h, 0.0)
            if self.sidereal:
                cusp_lon = (cusp_lon - self.ayanamsa) % 360.0
            sign_num = int(cusp_lon / 30) + 1
            if sign_num > 12:
                sign_num = 1
            self.house_signs[h] = sign_num
        
        # Dignities
        self.dignities = {}
        for name in self.planets.positions:
            if name in RULERSHIP.values():
                sign = self.planet_signs[name]["sign"]
                dignities = []
                
                # Rulership
                if RULERSHIP[sign] == name:
                    dignities.append("rulership")
                
                # Detriment
                if name in DETRIMENT:
                    det_sign = RULERSHIP.get(DETRIMENT[name])
                    # Simplified: detriment is opposite sign of rulership
                    ruler_signs = [s for s, r in RULERSHIP.items() if r == name]
                    for rs in ruler_signs:
                        opposite = (rs + 5) % 12 + 1
                        if opposite == sign:
                            dignities.append("detriment")
                
                # Exaltation
                if name in EXALTATION and EXALTATION[name] == sign:
                    dignities.append("exaltation")
                
                # Fall
                if name in FALL_SIGN and FALL_SIGN[name] == sign:
                    dignities.append("fall")
                
                self.dignities[name] = dignities or ["peregrine"]
        
        # Human Design gates (from tropical positions)
        self.hd_gates = {}
        for name, pos in self.planets.positions.items():
            if name in ["ASC", "MC", "LILITH", "CERES", "PALLAS", "JUNO", "VESTA"]:
                continue
            lon = pos.lon  # Always tropical for HD
            gate, line = self._lon_to_gate(lon)
            if gate:
                self.hd_gates[name] = {"gate": gate, "line": line}
        
        # Summary stats
        self.dominant_element = max(self.element_counts, key=self.element_counts.get)
        self.dominant_modality = max(self.modality_counts, key=self.modality_counts.get)
    
    def _lon_to_gate(self, lon: float):
        """Convert tropical longitude to Human Design gate and line."""
        # Gate 41 starts at 0° Aries (tropical)
        # Gate 1 starts at ~354.375° (end of Pisces)
        lon = lon % 360.0
        
        # Find gate
        gate = int((lon + 5.625 / 2) / 5.625) + 41
        if gate > 64:
            gate -= 64
        
        gate_start = GATE_DEGREES.get(gate, 0.0)
        offset = (lon - gate_start) % 360.0
        
        line = int(offset / GATE_LINE_DEGREE) + 1
        if line > 6:
            line = 6
        if line < 1:
            line = 1
        
        return gate, line
    
    def to_dict(self, compact: bool = False) -> dict:
        """Export chart as a dictionary.
        
        Args:
            compact: If True, skip detailed aspect list and HD gates
        """
        result = {
            "meta": {
                "datetime": self.dt.isoformat(),
                "lat": self.lat,
                "lon": self.lon,
                "house_system": self.house_system,
                "sidereal": self.sidereal,
                "ayanamsa": self.ayanamsa,
                "engine": "cosmos-engine",
            },
            "planets": {},
            "houses": self.houses.to_dict(),
            "angles": {
                "ascendant": self.houses.cusps.asc,
                "midheaven": self.houses.cusps.mc,
                "descendant": (self.houses.cusps.asc + 180.0) % 360.0,
                "ic": (self.houses.cusps.mc + 180.0) % 360.0,
            },
            "elements": self.element_counts,
            "modalities": self.modality_counts,
            "dominant": {
                "element": self.dominant_element,
                "modality": self.dominant_modality,
            },
            "dignities": self.dignities,
        }
        
        for name, pos in self.planets.positions.items():
            result["planets"][name] = {
                **pos.to_dict(),
                "sign_info": self.planet_signs.get(name, {}),
                "house": self.planet_houses.get(name, None),
                "dignity": self.dignities.get(name, ["peregrine"]),
            }
        
        if not compact:
            result["aspects"] = self.aspects.to_dict()
            result["hd_gates"] = self.hd_gates
        
        return result
    
    def __repr__(self):
        from .constants import SIGNS
        
        asc = self.houses.cusps.asc
        asc_sign = int(asc / 30) + 1
        if asc_sign > 12:
            asc_sign = 1
        asc_deg = int(asc % 30)
        asc_min = int((asc % 30 - asc_deg) * 60)
        
        mc = self.houses.cusps.mc
        mc_deg = int(mc % 30)
        mc_min = int((mc % 30 - mc_deg) * 60)
        
        lines = [
            f"Chart: {self.dt.strftime('%Y-%m-%d %H:%M')}",
            f"Location: {self.lat:.4f}, {self.lon:.4f}",
            f"ASC: {SIGNS[asc_sign]['symbol']} {asc_deg}°{asc_min}' | MC: {mc_deg}°{mc_min}'",
            f"House System: {self.house_system}",
            f"",
            "Planets:",
        ]
        
        planet_order = ["SUN", "MOON", "MERCURY", "VENUS", "MARS", 
                         "JUPITER", "SATURN", "URANUS", "NEPTUNE", "PLUTO",
                         "CHIRON", "NORTH_NODE"]
        
        for name in planet_order:
            if name in self.planet_signs:
                s = self.planet_signs[name]
                pos = self.planets.positions[name]
                d = int(s["degree"])
                m = int((s["degree"] - d) * 60)
                retro = " ℞" if pos.is_retrograde else ""
                house = self.planet_houses.get(name, "?")
                dig = ", ".join(self.dignities.get(name, []))
                lines.append(f"  {name:12s} {s['sign_symbol']} {d:2d}°{m:02d}'{retro:2s} | House {house:2d} | {dig}")
        
        lines.append(f"\nElements: {self.element_counts} → Dominant: {self.dominant_element}")
        lines.append(f"Modalities: {self.modality_counts} → Dominant: {self.dominant_modality}")
        
        lines.append(f"\nAspects ({len(self.aspects.aspects)} total):")
        for a in self.aspects.aspects[:20]:  # Top 20
            lines.append(f"  {a}")
        if len(self.aspects.aspects) > 20:
            lines.append(f"  ... and {len(self.aspects.aspects) - 20} more")
        
        if self.hd_gates:
            lines.append(f"\nHD Gates:")
            for name in planet_order:
                if name in self.hd_gates:
                    g = self.hd_gates[name]
                    lines.append(f"  {name:12s} Gate {g['gate']}.{g['line']}")
        
        return "\n".join(lines)


# CLI
if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python -m cosmos.chart '1997-02-19T10:09:00+01:00' [lat] [lon] [house_system]")
        print("Example: python -m cosmos.chart '1997-02-19T10:09:00+01:00' 48.1486 17.1077 P")
        sys.exit(1)
    
    dt = datetime.fromisoformat(sys.argv[1])
    lat = float(sys.argv[2]) if len(sys.argv) > 2 else 48.1486
    lon = float(sys.argv[3]) if len(sys.argv) > 3 else 17.1077
    hsys = sys.argv[4] if len(sys.argv) > 4 else "P"
    
    chart = Chart(dt, lat, lon, house_system=hsys)
    
    if "--json" in sys.argv:
        compact = "--compact" in sys.argv
        print(json.dumps(chart.to_dict(compact=compact), indent=2))
    else:
        print(chart)
