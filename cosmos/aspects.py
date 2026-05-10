"""
Aspect calculation between planets.

Detects all major and minor aspects between planetary pairs,
including custom orbs and aspect types.
"""

import math
from typing import Optional

from .constants import ASPECTS, PLANETS


class Aspect:
    """A single aspect between two planets."""
    
    def __init__(self, planet1: str, planet2: str, aspect_type: str,
                 angle: float, orb: float, actual_angle: float):
        self.planet1 = planet1
        self.planet2 = planet2
        self.aspect_type = aspect_type
        self.angle = angle          # Ideal angle
        self.orb = orb              # Allowed orb
        self.actual_angle = actual_angle  # Actual angular separation
        self.deviation = abs(actual_angle - angle)
        if self.deviation > 180.0:
            self.deviation = 360.0 - self.deviation
        self.applying = None  # Set externally if speed data available
    
    def to_dict(self) -> dict:
        return {
            "planet1": self.planet1,
            "planet2": self.planet2,
            "aspect": self.aspect_type,
            "angle": round(self.angle, 2),
            "orb": round(self.orb, 2),
            "actual_angle": round(self.actual_angle, 4),
            "deviation": round(self.deviation, 4),
            "applying": self.applying,
        }
    
    def __repr__(self):
        symbol = ASPECTS.get(self.aspect_type, {}).get("symbol", "?")
        direction = ""
        if self.applying is True:
            direction = " (applying)"
        elif self.applying is False:
            direction = " (separating)"
        return f"<{self.planet1} {symbol} {self.planet2} {self.aspect_type} orb={self.deviation:.2f}°{direction}>"


class AspectEngine:
    """Calculate all aspects between a set of planetary positions."""
    
    def __init__(self, positions: dict, custom_orbs: Optional[dict] = None):
        """
        Args:
            positions: Dict of planet_name -> PlanetPosition or dict with 'longitude' key
            custom_orbs: Optional dict of aspect_type -> orb override
        """
        self.positions = positions
        self.custom_orbs = custom_orbs or {}
        self.aspects: list[Aspect] = []
        self._calculate()
    
    def _get_lon(self, name: str) -> float:
        """Get ecliptic longitude for a planet."""
        pos = self.positions.get(name)
        if pos is None:
            return 0.0
        if hasattr(pos, 'lon'):
            return pos.lon
        return pos.get('longitude', 0.0)
    
    def _get_speed(self, name: str) -> float:
        """Get daily speed for a planet (for applying/separating)."""
        pos = self.positions.get(name)
        if pos is None:
            return 0.0
        if hasattr(pos, 'speed_lon'):
            return pos.speed_lon
        return pos.get('speed', 0.0)
    
    def _angular_separation(self, lon1: float, lon2: float) -> float:
        """Calculate angular separation between two longitudes (0-180°)."""
        diff = abs(lon1 - lon2) % 360.0
        if diff > 180.0:
            diff = 360.0 - diff
        return diff
    
    def _calculate(self):
        """Find all aspects between all planet pairs."""
        planet_names = list(self.positions.keys())
        
        for i, p1 in enumerate(planet_names):
            for p2 in planet_names[i + 1:]:
                lon1 = self._get_lon(p1)
                lon2 = self._get_lon(p2)
                
                separation = self._angular_separation(lon1, lon2)
                
                for aspect_name, aspect_data in ASPECTS.items():
                    orb = self.custom_orbs.get(aspect_name, aspect_data["orb"])
                    ideal = aspect_data["angle"]
                    
                    deviation = abs(separation - ideal)
                    if deviation > 180.0:
                        deviation = 360.0 - deviation
                    
                    if deviation <= orb:
                        # Determine applying/separating
                        speed1 = self._get_speed(p1)
                        speed2 = self._get_speed(p2)
                        applying = None
                        if speed1 != 0.0 or speed2 != 0.0:
                            # If the faster planet is approaching the slower one
                            rel_speed = speed2 - speed1
                            if rel_speed != 0:
                                if aspect_data["angle"] < 180.0:
                                    current = (lon2 - lon1) % 360.0
                                    if current > 180.0:
                                        current -= 360.0
                                    ideal_signed = aspect_data["angle"]
                                    if current < ideal_signed:
                                        applying = rel_speed > 0
                                    else:
                                        applying = rel_speed < 0
                        
                        aspect = Aspect(
                            planet1=p1, planet2=p2,
                            aspect_type=aspect_name,
                            angle=ideal,
                            orb=orb,
                            actual_angle=separation,
                        )
                        aspect.applying = applying
                        self.aspects.append(aspect)
        
        # Sort by aspect type priority
        aspect_order = {
            "conjunction": 0, "opposition": 1, "trine": 2, "square": 3,
            "sextile": 4, "quincunx": 5, "semisquare": 6, "sesquiquadrate": 7,
            "semisextile": 8, "quintile": 9, "biquintile": 10,
        }
        self.aspects.sort(key=lambda a: (aspect_order.get(a.aspect_type, 99), a.deviation))
    
    def get_by_planet(self, planet_name: str) -> list[Aspect]:
        """Get all aspects involving a specific planet."""
        return [a for a in self.aspects 
                if a.planet1 == planet_name or a.planet2 == planet_name]
    
    def get_by_type(self, aspect_type: str) -> list[Aspect]:
        """Get all aspects of a specific type."""
        return [a for a in self.aspects if a.aspect_type == aspect_type]
    
    def to_dict(self) -> list[dict]:
        return [a.to_dict() for a in self.aspects]
    
    def __repr__(self):
        if not self.aspects:
            return "<No aspects>"
        lines = [f"Aspects ({len(self.aspects)}):"]
        for a in self.aspects:
            lines.append(f"  {a}")
        return "\n".join(lines)


# Test
if __name__ == "__main__":
    test_positions = {
        "SUN": type('obj', (), {'lon': 0.0, 'speed_lon': 1.0})(),
        "MOON": type('obj', (), {'lon': 90.0, 'speed_lon': 13.0})(),
        "MARS": type('obj', (), {'lon': 120.5, 'speed_lon': 0.5})(),
        "SATURN": type('obj', (), {'lon': 180.0, 'speed_lon': 0.1})(),
    }
    engine = AspectEngine(test_positions)
    print(engine)
