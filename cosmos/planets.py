"""
Planetary position calculation using Skyfield + JPL ephemerides.

Skyfield: MIT license
JPL DE440/DE421 ephemerides: Public domain (NASA/JPL)
Combined: Fully commercial-usable, zero Swiss Ephemeris dependency.
"""

import math
from datetime import datetime, timezone
from typing import Optional

from skyfield.api import load, Loader
from skyfield.framelib import ecliptic_frame
from skyfield.nutationlib import iau2000b

from .constants import PLANETS, SKYFIELD_PLANETS

# Singleton loader
_loader = Loader("/tmp/skyfield_cache")
_ts = None
_planets = None


def _init_ephemeris(ephemeris_path: str = "/tmp/hd-research/de421.bsp"):
    """Initialize Skyfield with JPL ephemeris file.
    
    Args:
        ephemeris_path: Path to .bsp ephemeris file.
                       DE421 covers 1900-2050. DE440 covers 1550-2650.
    """
    global _planets, _ts
    if _planets is not None:
        return
    
    _planets = _loader(ephemeris_path)
    _ts = _loader.timescale()


def _get_skyfield_time(dt: datetime):
    """Convert Python datetime to Skyfield time."""
    if _ts is None:
        _init_ephemeris()
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return _ts.from_datetime(dt)


def _dms_to_decimal(dms_str: str) -> float:
    """Convert DMS string like '23°46'25.3"' to decimal degrees."""
    import re
    parts = re.findall(r'[\d.]+', dms_str)
    if len(parts) >= 3:
        d, m, s = float(parts[0]), float(parts[1]), float(parts[2])
    elif len(parts) == 2:
        d, m, s = float(parts[0]), float(parts[1]), 0.0
    else:
        return float(parts[0])
    
    sign = -1 if d < 0 else 1
    return sign * (abs(d) + m / 60.0 + s / 3600.0)


class PlanetPosition:
    """Position data for a single planet at a given time."""
    
    def __init__(self, name: str, lon: float, lat: float, distance: float,
                 speed_lon: float = 0.0, is_retrograde: bool = False,
                 ra: float = 0.0, dec: float = 0.0):
        self.name = name
        self.lon = lon          # Ecliptic longitude (degrees 0-360)
        self.lat = lat          # Ecliptic latitude
        self.distance = distance # AU
        self.speed_lon = speed_lon  # degrees/day
        self.is_retrograde = is_retrograde
        self.ra = ra            # Right Ascension (degrees)
        self.dec = dec          # Declination (degrees)
        
        # Compute sign
        self.sign_num = int(lon / 30) + 1
        if self.sign_num > 12:
            self.sign_num = 1
        self.sign_degree = lon % 30
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "longitude": round(self.lon, 6),
            "latitude": round(self.lat, 6),
            "distance": round(self.distance, 6),
            "speed": round(self.speed_lon, 6),
            "retrograde": self.is_retrograde,
            "sign": self.sign_num,
            "sign_degree": round(self.sign_degree, 6),
            "ra": round(self.ra, 6),
            "dec": round(self.dec, 6),
        }
    
    def __repr__(self):
        from .constants import SIGNS
        s = SIGNS[self.sign_num]
        d = int(self.sign_degree)
        m = int((self.sign_degree - d) * 60)
        s_sec = int(((self.sign_degree - d) * 60 - m) * 60)
        return f"<{self.name} {s['symbol']} {d}°{m}'{s_sec}\" {'℞' if self.is_retrograde else ''}>"


class PlanetPositions:
    """Calculate all planetary positions for a given datetime."""
    
    def __init__(self, dt: datetime, ephemeris_path: str = "/tmp/hd-research/de421.bsp",
                 use_heliocentric: bool = False):
        self.dt = dt
        self.heliocentric = use_heliocentric
        _init_ephemeris(ephemeris_path)
        
        self.earth = _planets['earth']
        self.positions: dict[str, PlanetPosition] = {}
        self._calculate()
    
    def _calculate(self):
        """Calculate positions for all planets."""
        t = _get_skyfield_time(self.dt)
        
        for name, skyfield_name in SKYFIELD_PLANETS.items():
            try:
                body = _planets[skyfield_name]
                
                if self.heliocentric:
                    # Position from Sun
                    astrometric = body.at(t)
                else:
                    # Position from Earth (geocentric)
                    astrometric = self.earth.at(t).observe(body)
                
                # Get ecliptic coordinates
                lat, lon, distance = astrometric.frame_latlon(ecliptic_frame)
                
                # Convert to degrees
                lon_deg = lon.degrees % 360.0
                lat_deg = lat.degrees
                dist_au = distance.au
                
                # Right Ascension and Declination
                ra, dec, _ = astrometric.radec()
                
                self.positions[name] = PlanetPosition(
                    name=name,
                    lon=lon_deg,
                    lat=lat_deg,
                    distance=dist_au,
                    ra=ra.hours * 15.0,  # Convert hours to degrees
                    dec=dec.degrees,
                )
                
            except Exception as e:
                # Skip planets not in the ephemeris file
                continue
        
        # Calculate North Node (mean node)
        self._calculate_nodes(t)
        
        # Calculate Chiron
        self._calculate_chiron(t)
    
    def _calculate_nodes(self, t):
        """Calculate lunar nodes (mean node approximation).
        
        Uses the Meeus formula for mean lunar node longitude.
        Accuracy: ~0.5° (good enough for most astrology, within orb).
        """
        # Julian centuries since J2000.0
        jd = t.tt
        T = (jd - 2451545.0) / 36525.0
        
        # Mean longitude of the ascending node (Meeus, Astronomical Algorithms)
        # Formula: 125.04452 - 1934.136261 * T + 0.0020708 * T^2 + T^3/450000
        node_lon = 125.04452 - 1934.136261 * T + 0.0020708 * T * T + T * T * T / 450000.0
        node_lon = node_lon % 360.0
        
        # South node is opposite
        south_lon = (node_lon + 180.0) % 360.0
        
        self.positions["NORTH_NODE"] = PlanetPosition(
            name="NORTH_NODE", lon=node_lon, lat=0.0, distance=0.0
        )
        self.positions["SOUTH_NODE"] = PlanetPosition(
            name="SOUTH_NODE", lon=south_lon, lat=0.0, distance=0.0
        )
    
    def _calculate_chiron(self, t):
        """Calculate Chiron position (mean orbital elements approximation).
        
        Accuracy: ~0.5-1° (orbital elements not full integration).
        For precise Chiron, use a longer ephemeris file or full orbital integration.
        """
        # Chiron orbital elements (J2000.0, epoch 2020 approx)
        # Using mean elements from JPL Small-Body Database
        jd = t.tt
        d = jd - 2451545.0  # Days since J2000.0
        
        # Mean elements for Chiron (approximate)
        a = 13.666       # Semi-major axis (AU)
        e = 0.380        # Eccentricity
        i = 6.935        # Inclination (degrees)
        node = 209.281    # Longitude of ascending node
        peri = 339.398    # Argument of perihelion
        M0 = 153.6        # Mean anomaly at epoch
        
        # Mean motion (degrees/day)
        n = 0.0193  # ~50.7 year period
        
        # Mean anomaly
        M = (M0 + n * d) % 360.0
        M_rad = math.radians(M)
        
        # Solve Kepler's equation (simple iteration)
        E = M_rad
        for _ in range(10):
            E = M_rad + e * math.sin(E)
        
        # True anomaly
        cos_E = math.cos(E)
        sin_E = math.sin(E)
        true_anom = math.atan2(
            math.sqrt(1 - e * e) * sin_E,
            cos_E - e
        )
        
        # Heliocentric distance
        r = a * (1 - e * math.cos(E))
        
        # Convert to heliocentric ecliptic coordinates
        node_rad = math.radians(node)
        peri_rad = math.radians(peri)
        i_rad = math.radians(i)
        
        arg = peri_rad + true_anom
        sin_arg = math.sin(arg)
        cos_arg = math.cos(arg)
        
        x = r * (math.cos(node_rad) * cos_arg - math.sin(node_rad) * sin_arg * math.cos(i_rad))
        y = r * (math.sin(node_rad) * cos_arg + math.cos(node_rad) * sin_arg * math.cos(i_rad))
        z = r * sin_arg * math.sin(i_rad)
        
        # Convert to geocentric (approximate — assume Earth at 1 AU)
        # Get Earth position
        earth = _planets['earth'].at(t)
        _, earth_lon, earth_dist = earth.frame_latlon(ecliptic_frame)
        
        earth_x = earth_dist.au * math.cos(math.radians(earth_lon.degrees))
        earth_y = earth_dist.au * math.sin(math.radians(earth_lon.degrees))
        
        # Geocentric position
        geo_x = x - earth_x
        geo_y = y - earth_y
        
        lon_deg = math.degrees(math.atan2(geo_y, geo_x)) % 360.0
        geo_dist = math.sqrt(geo_x * geo_x + geo_y * geo_y + z * z)
        
        # Ecliptic latitude
        lat_deg = math.degrees(math.asin(z / geo_dist)) if geo_dist > 0 else 0.0
        
        self.positions["CHIRON"] = PlanetPosition(
            name="CHIRON", lon=lon_deg, lat=lat_deg, distance=geo_dist
        )
    
    def get(self, name: str) -> Optional[PlanetPosition]:
        return self.positions.get(name)
    
    def to_dict(self) -> dict:
        return {
            name: pos.to_dict()
            for name, pos in self.positions.items()
        }
    
    def __repr__(self):
        lines = [f"Planetary Positions @ {self.dt.isoformat()}"]
        for name in ["SUN", "MOON", "MERCURY", "VENUS", "MARS", "JUPITER", 
                      "SATURN", "URANUS", "NEPTUNE", "PLUTO", "NORTH_NODE"]:
            pos = self.positions.get(name)
            if pos:
                lines.append(f"  {pos}")
        return "\n".join(lines)


# Quick test
if __name__ == "__main__":
    # Test: Sun position on known date
    dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    pp = PlanetPositions(dt)
    sun = pp.get("SUN")
    print(f"Sun on 2024-01-01: {sun}")
    print(f"Expected: ~10° Capricorn")
    
    moon = pp.get("MOON")
    print(f"Moon: {moon}")
    
    nn = pp.get("NORTH_NODE")
    print(f"North Node: {nn}")
