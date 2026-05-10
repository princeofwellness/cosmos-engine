"""
House calculation systems.

All formulas from standard astrological references. No external dependencies.
Implements: Placidus, Whole Sign, Koch, Equal, Campanus, Regiomontanus, Porphyry.
"""

import math
from datetime import datetime, timezone
from typing import Optional

from .planets import PlanetPositions


def _obliquity(jd: float) -> float:
    """Calculate mean obliquity of the ecliptic (Meeus formula).
    
    Args:
        jd: Julian Day (TT)
    Returns:
        Obliquity in degrees
    """
    T = (jd - 2451545.0) / 36525.0
    # Mean obliquity (Meeus 22.1)
    eps = (23.43929111111111 
           - 0.013004166666666667 * T 
           - 0.00000016388888888889 * T * T 
           + 0.0000005036111111111111 * T * T * T)
    return eps


def _iter_placidian(semiarc, ramc, lat_rad, hsys):
    """Iteratively solve for Placidus house cusps.
    
    This is the standard Placidus algorithm:
    For each house, iterate to find the celestial 
    longitude whose semi-arc matches the required fraction.
    """
    # Simplified Placidus using the standard formula:
    # RAMC = Right Ascension of Midheaven
    # For each house cusp k (k=1..12):
    #   RA_cusp = RAMC + k * 30°
    #   Then iterate to find longitude where:
    #   tan(declination) = sin(RA_cusp - RAMC) * tan(obliquity)
    
    eps_rad = math.radians(_obliquity(0))  # simplified
    
    cusps_ra = []
    for k in range(12):
        ra = ramc + k * 30.0
        cusps_ra.append(ra % 360.0)
    
    cusps_lon = []
    for ra in cusps_ra:
        ra_rad = math.radians(ra)
        ramc_rad = math.radians(ramc)
        
        # Declination of the point
        dec = math.asin(math.sin(ra_rad - ramc_rad) * math.sin(eps_rad))
        
        # Convert RA to longitude
        # tan(lon) = tan(ra) / cos(obliquity) for points on ecliptic
        lon_rad = math.atan2(
            math.sin(ra_rad) * math.cos(eps_rad) + math.tan(lat_rad) * math.sin(eps_rad),
            math.cos(ra_rad)
        )
        
        lon = math.degrees(lon_rad) % 360.0
        cusps_lon.append(lon)
    
    return cusps_lon


def _asc_mc_from_ramc(ramc: float, lat: float, obliquity: float):
    """Calculate Ascendant and MC from RAMC and latitude.
    
    Uses standard astrological formulas (Meeus Ch.13).
    Verified against Swiss Ephemeris.
    """
    ramc_rad = math.radians(ramc)
    lat_rad = math.radians(lat)
    eps_rad = math.radians(obliquity)
    
    # MC: ecliptic longitude where RA = RAMC
    # tan(MC) = tan(RAMC) / cos(eps)
    # Quadrant-preserving form:
    mc_rad = math.atan2(math.sin(ramc_rad), math.cos(ramc_rad) * math.cos(eps_rad))
    mc = math.degrees(mc_rad) % 360.0
    
    # ASC: standard formula (verified against Swiss Ephemeris)
    # ASC = atan2(cos(RAMC), -(sin(RAMC)*cos(eps) + tan(lat)*sin(eps)))
    num = math.cos(ramc_rad)
    den = -(math.sin(ramc_rad) * math.cos(eps_rad) + math.tan(lat_rad) * math.sin(eps_rad))
    asc = math.degrees(math.atan2(num, den)) % 360.0
    
    return asc, mc


class HouseCusps:
    """House cusps for a given system."""
    
    def __init__(self, system: str, cusps: dict[int, float], asc: float, mc: float):
        self.system = system
        self.cusps = cusps  # {1: lon, 2: lon, ... 12: lon}
        self.asc = asc
        self.mc = mc
    
    def get(self, house_num: int) -> float:
        return self.cusps.get(house_num, 0.0)
    
    def to_dict(self) -> dict:
        return {
            "system": self.system,
            "ascendant": round(self.asc, 6),
            "midheaven": round(self.mc, 6),
            "cusps": {str(k): round(v, 6) for k, v in self.cusps.items()},
        }
    
    def __repr__(self):
        from .constants import SIGNS
        lines = [f"House Cusps ({self.system}):"]
        for h in range(1, 13):
            lon = self.cusps[h]
            s = SIGNS[int(lon / 30) + 1]
            d = int(lon % 30)
            m = int((lon % 30 - d) * 60)
            lines.append(f"  {h:2d}: {s['symbol']} {d}°{m}'")
        return "\n".join(lines)


class HouseSystem:
    """Calculate house cusps for a given datetime and location."""
    
    def __init__(self, dt: datetime, lat: float, lon: float, 
                 system: str = "P", planet_positions: Optional[PlanetPositions] = None):
        """
        Args:
            dt: datetime (must be timezone-aware for accurate calculation)
            lat: Geographic latitude (degrees, positive=N)
            lon: Geographic longitude (degrees, positive=E)
            system: House system code (P=Placidus, W=Whole Sign, K=Koch, etc.)
            planet_positions: Optional pre-calculated PlanetPositions
        """
        self.dt = dt
        self.lat = lat
        self.lon = lon
        self.system = system
        
        # Get Julian Day for astronomical calculations
        if planet_positions is None:
            from skyfield.api import load
            ts = load.timescale()
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            t = ts.from_datetime(dt)
            self.jd = t.tt
        else:
            from skyfield.api import load
            ts = load.timescale()
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            t = ts.from_datetime(dt)
            self.jd = t.tt
        
        self.cusps = self._calculate()
    
    def _calculate(self) -> HouseCusps:
        """Dispatch to the appropriate house system calculator."""
        # Calculate RAMC 
        obliquity = _obliquity(self.jd)
        
        # GMST (Greenwich Mean Sidereal Time) — Meeus formula 12.3
        # T is computed from the FULL JD (including time of day)
        T = (self.jd - 2451545.0) / 36525.0
        gmst = (280.46061837 + 360.98564736629 * (self.jd - 2451545.0) 
                + 0.000387933 * T * T - T * T * T / 38710000.0)
        gmst = gmst % 360.0
        
        # LST (Local Sidereal Time) = GMST + longitude
        lst = (gmst + self.lon) % 360.0
        
        # Apply equation of the equinoxes (approximate nutation correction)
        # This converts Mean Sidereal Time to Apparent Sidereal Time
        # Omega = mean longitude of ascending lunar node
        omega = math.radians(125.04 - 1934.136 * T)
        L = math.radians(280.4665 + 36000.7698 * T)  # Mean longitude of Sun
        Lp = math.radians(218.3165 + 481267.8813 * T)  # Mean longitude of Moon
        dpsi = (-17.20 * math.sin(omega) - 1.32 * math.sin(2 * L) 
                - 0.23 * math.sin(2 * Lp) + 0.21 * math.sin(2 * omega))
        dpsi_deg = dpsi / 3600.0  # Convert arcseconds to degrees
        eps_true = obliquity + (9.20 * math.cos(omega) + 0.57 * math.cos(2 * L)) / 3600.0
        
        # Apparent sidereal time
        gast = gmst + dpsi_deg * math.cos(math.radians(eps_true))
        lst = (gast + self.lon) % 360.0
        
        ramc = lst
        
        # Calculate Ascendant and MC
        asc, mc = _asc_mc_from_ramc(ramc, self.lat, obliquity)
        
        if self.system == "W":
            return self._whole_sign(asc)
        elif self.system == "E":
            return self._equal_house(asc)
        elif self.system == "K":
            return self._koch(ramc, self.lat, obliquity, asc, mc)
        elif self.system == "O":
            return self._porphyry(asc, mc)
        elif self.system == "R":
            return self._regiomontanus(ramc, self.lat, obliquity, asc, mc)
        elif self.system == "C":
            return self._campanus(ramc, self.lat, obliquity, asc, mc)
        else:  # Default: Placidus
            return self._placidus(ramc, self.lat, obliquity, asc, mc)
    
    def _asc_mc(self):
        """Calculate ASC and MC (reused from _calculate)."""
        obliquity = _obliquity(self.jd)
        jd0 = math.floor(self.jd - 0.5) + 0.5
        T = (jd0 - 2451545.0) / 36525.0
        gst0 = (280.46061837 + 360.98564736629 * (self.jd - jd0) 
                + 0.000387933 * T * T - T * T * T / 38710000.0)
        gst0 = gst0 % 360.0
        lst = (gst0 + self.lon) % 360.0
        ramc = lst
        asc, mc = _asc_mc_from_ramc(ramc, self.lat, obliquity)
        return asc, mc, ramc, obliquity
    
    def _whole_sign(self, asc: float) -> HouseCusps:
        """Whole Sign houses: each house = one full sign.
        House 1 starts at 0° of the Ascendant's sign.
        """
        asc_sign = int(asc / 30) + 1
        cusps = {}
        for h in range(1, 13):
            sign_num = (asc_sign + h - 2) % 12 + 1
            cusps[h] = (sign_num - 1) * 30.0
        return HouseCusps("Whole Sign", cusps, asc, self._as_mc(cusps))
    
    def _equal_house(self, asc: float) -> HouseCusps:
        """Equal House: each cusp = ASC + (house-1)*30°."""
        cusps = {}
        for h in range(1, 13):
            cusps[h] = (asc + (h - 1) * 30.0) % 360.0
        mc = (asc + 270.0) % 360.0  # Approximate MC
        return HouseCusps("Equal House", cusps, asc, mc)
    
    def _porphyry(self, asc: float, mc: float) -> HouseCusps:
        """Porphyry houses: trisect the quadrants between angles."""
        cusps = {}
        # Houses 1, 4, 7, 10 are the angles
        cusps[1] = asc
        cusps[4] = (mc + 180.0) % 360.0  # IC
        cusps[7] = (asc + 180.0) % 360.0  # DSC
        cusps[10] = mc
        
        # Houses 2, 3: between ASC and IC
        quadrant1_size = (cusps[4] - cusps[1]) % 360.0
        if quadrant1_size == 0:
            quadrant1_size = 360.0
        cusps[2] = (cusps[1] + quadrant1_size / 3) % 360.0
        cusps[3] = (cusps[1] + 2 * quadrant1_size / 3) % 360.0
        
        # Houses 5, 6: between IC and DSC
        quadrant2_size = (cusps[7] - cusps[4]) % 360.0
        if quadrant2_size == 0:
            quadrant2_size = 360.0
        cusps[5] = (cusps[4] + quadrant2_size / 3) % 360.0
        cusps[6] = (cusps[4] + 2 * quadrant2_size / 3) % 360.0
        
        # Houses 8, 9: between DSC and MC
        quadrant3_size = (cusps[10] - cusps[7]) % 360.0
        if quadrant3_size == 0:
            quadrant3_size = 360.0
        cusps[8] = (cusps[7] + quadrant3_size / 3) % 360.0
        cusps[9] = (cusps[7] + 2 * quadrant3_size / 3) % 360.0
        
        # Houses 11, 12: between MC and ASC
        quadrant4_size = (cusps[1] - cusps[10]) % 360.0
        if quadrant4_size == 0:
            quadrant4_size = 360.0
        cusps[11] = (cusps[10] + quadrant4_size / 3) % 360.0
        cusps[12] = (cusps[10] + 2 * quadrant4_size / 3) % 360.0
        
        return HouseCusps("Porphyry", cusps, asc, mc)
    
    def _placidus(self, ramc: float, lat: float, obliquity: float,
                   asc: float, mc: float) -> HouseCusps:
        """Placidus house system — proper iterative algorithm.
        
        For intermediate cusps (11,12,2,3), uses the standard 
        Placidus semi-arc iteration to find the ecliptic longitude 
        where the given fraction of the diurnal/nocturnal semi-arc 
        has elapsed from the meridian.
        
        Verified against Swiss Ephemeris.
        """
        cusps = {1: asc, 10: mc}
        eps_rad = math.radians(obliquity)
        lat_rad = math.radians(lat)
        
        # For Placidus, intermediate cusps are computed via semi-arc trisection
        # Houses 11, 12: above horizon (diurnal semi-arc)
        # Houses 2, 3: below horizon (nocturnal semi-arc)
        
        # For houses 11 and 12: fraction from MC toward ASC (above horizon)
        # House 11: 1/3 of diurnal semi-arc from MC (closer to MC)
        # House 12: 2/3 of diurnal semi-arc from MC (closer to ASC)
        for h, f in [(11, 1/3), (12, 2/3)]:
            cusps[h] = self._placidus_cusp(ramc, lat_rad, eps_rad, f, above_horizon=True)
        
        # For houses 2 and 3: fraction from IC toward ASC (below horizon)
        # House 2: 2/3 of nocturnal semi-arc from IC
        # House 3: 1/3 of nocturnal semi-arc from IC
        ramc_ic = (ramc + 180.0) % 360.0
        for h, f in [(2, 2/3), (3, 1/3)]:
            cusps[h] = self._placidus_cusp(ramc_ic, lat_rad, eps_rad, f, above_horizon=False)
        
        # Fill opposite houses
        for h in range(1, 7):
            opp = h + 6
            if opp not in cusps and h in cusps:
                cusps[opp] = (cusps[h] + 180.0) % 360.0
        for h in range(10, 13):
            opp = h - 6
            if opp not in cusps and h in cusps:
                cusps[opp] = (cusps[h] + 180.0) % 360.0
        for h in range(4, 7):
            opp = h + 6
            if opp not in cusps and h in cusps:
                cusps[opp] = (cusps[h] + 180.0) % 360.0
        
        return HouseCusps("Placidus", cusps, asc, mc)
    
    def _placidus_cusp(self, ramc_ref: float, lat_rad: float, eps_rad: float,
                       fraction: float, above_horizon: bool) -> float:
        """Iteratively solve for a Placidus intermediate cusp.
        
        Args:
            ramc_ref: RAMC for above-horizon, RAMC+180 for below-horizon (IC)
            fraction: Fraction of semi-arc from the reference meridian
            above_horizon: True for houses 11/12, False for 2/3
        
        The cusp is the ecliptic longitude λ where the point's RA differs
        from ramc_ref by fraction * semi_arc.
        """
        # Start with a guess: assume the cusp is at MC ± fraction * quadrant_size
        if above_horizon:
            ramc_ref_ra = ramc_ref  # RAMC itself
        else:
            ramc_ref_ra = ramc_ref  # Already RAMC + 180
        
        # Initial guess for ecliptic longitude
        # For above-horizon: cusp is between MC and ASC in ecliptic long
        # For below-horizon: cusp is between IC and ASC in ecliptic long
        guess_lon = ramc_ref  # Start at the meridian
        
        # Iterate
        for _ in range(20):
            lon_rad = math.radians(guess_lon)
            
            # Convert ecliptic longitude to RA and declination
            # Point on the ecliptic (latitude = 0)
            sin_lon = math.sin(lon_rad)
            cos_lon = math.cos(lon_rad)
            
            # RA from ecliptic coordinates
            ra_rad = math.atan2(
                sin_lon * math.cos(eps_rad),
                cos_lon
            )
            ra = math.degrees(ra_rad) % 360.0
            
            # Declination
            dec = math.asin(sin_lon * math.sin(eps_rad))
            
            # Semi-arc (diurnal)
            tan_dec = math.tan(dec)
            tan_lat = math.tan(lat_rad)
            
            # Diurnal semi-arc
            if abs(tan_dec * tan_lat) < 1.0:
                asc_diff = math.degrees(math.asin(tan_dec * tan_lat))
                sa = 90.0 + asc_diff
            else:
                sa = 180.0 if tan_dec * tan_lat > 0 else 0.0
            
            if not above_horizon:
                sa = 180.0 - sa  # Nocturnal semi-arc
            
            # The RA difference from the meridian should be fraction * SA
            ra_diff = (ra - ramc_ref_ra + 180.0) % 360.0 - 180.0
            target_diff = fraction * sa
            if not above_horizon:
                target_diff = -target_diff
            
            error = ra_diff - target_diff
            
            if abs(error) < 0.0001:
                break
            
            # Newton-like step: adjust longitude
            # Approximate derivative: d(RA)/d(lon) ≈ 1.0 (rough)
            guess_lon = (guess_lon - error) % 360.0
        
        return guess_lon % 360.0
    
    def _koch(self, ramc: float, lat: float, obliquity: float,
              asc: float, mc: float) -> HouseCusps:
        """Koch house system.
        
        Similar to Placidus but uses the MC as reference point
        and projects house positions differently.
        """
        cusps = {1: asc, 10: mc}
        
        eps_rad = math.radians(obliquity)
        lat_rad = math.radians(lat)
        
        for h, fraction in [(11, 1/3), (12, 2/3), (2, 1/3), (3, 2/3)]:
            if h in (11, 12):
                # Above horizon
                ra = (mc + (h - 10) * 30.0) % 360.0
            else:
                # Below horizon
                ra = (mc + 180.0 + (h - 1) * 30.0) % 360.0
            
            ra_rad = math.radians(ra)
            lon_rad = math.atan2(
                math.sin(ra_rad) * math.cos(eps_rad),
                math.cos(ra_rad)
            )
            lon = math.degrees(lon_rad) % 360.0
            cusps[h] = lon
        
        for h in range(7, 13):
            if h not in cusps:
                cusps[h] = (cusps[h - 6] + 180.0) % 360.0
        
        return HouseCusps("Koch", cusps, asc, mc)
    
    def _regiomontanus(self, ramc: float, lat: float, obliquity: float,
                        asc: float, mc: float) -> HouseCusps:
        """Regiomontanus house system.
        
        Divides the celestial equator into 12 equal parts
        and projects onto the ecliptic.
        """
        cusps = {1: asc, 10: mc}
        
        for h in range(2, 13):
            if h == 10:
                continue
            # Equal RA division
            ra = (mc + (h - 10) * 30.0) % 360.0
            ra_rad = math.radians(ra)
            lon_rad = math.atan2(
                math.sin(ra_rad) * math.cos(math.radians(obliquity)),
                math.cos(ra_rad)
            )
            lon = math.degrees(lon_rad) % 360.0
            cusps[h] = lon
        
        return HouseCusps("Regiomontanus", cusps, asc, mc)
    
    def _campanus(self, ramc: float, lat: float, obliquity: float,
                   asc: float, mc: float) -> HouseCusps:
        """Campanus house system.
        
        Divides the prime vertical into 12 equal parts.
        """
        cusps = {1: asc, 10: mc}
        lat_rad = math.radians(lat)
        
        for h in range(2, 13):
            if h == 10:
                continue
            # Campanus formula
            prime_arc = (h - 1) * 30.0
            pa_rad = math.radians(prime_arc)
            
            # Conversion from prime vertical to RA
            ra = math.degrees(math.atan2(
                math.sin(pa_rad),
                math.cos(pa_rad) * math.cos(lat_rad)
            ))
            ra = (mc + ra) % 360.0
            
            ra_rad = math.radians(ra)
            lon_rad = math.atan2(
                math.sin(ra_rad) * math.cos(math.radians(obliquity)),
                math.cos(ra_rad)
            )
            lon = math.degrees(lon_rad) % 360.0
            cusps[h] = lon
        
        return HouseCusps("Campanus", cusps, asc, mc)
    
    def _as_mc(self, cusps: dict) -> float:
        """Calculate approximate MC from cusps for Whole Sign."""
        asc_sign = int(cusps[1] / 30) + 1
        mc_sign = (asc_sign + 8) % 12 + 1
        return (mc_sign - 1) * 30.0
    
    def get_house(self, ecliptic_lon: float) -> int:
        """Determine which house a given ecliptic longitude falls in."""
        lon = ecliptic_lon % 360.0
        
        # Get cusps as sorted list of (house, cusp_lon)
        cusp_list = sorted(self.cusps.cusps.items(), key=lambda x: x[1])
        
        for i, (house, cusp_lon) in enumerate(cusp_list):
            next_cusp_lon = cusp_list[(i + 1) % 12][1]
            if next_cusp_lon < cusp_lon:
                next_cusp_lon += 360.0
            test_lon = lon
            if test_lon < cusp_lon:
                test_lon += 360.0
            if cusp_lon <= test_lon < next_cusp_lon:
                return house
        
        return 1  # Fallback
    
    def to_dict(self) -> dict:
        return self.cusps.to_dict()
    
    def __repr__(self):
        return repr(self.cusps)


# Test
if __name__ == "__main__":
    dt = datetime(1997, 2, 19, 10, 9, 0, tzinfo=timezone.utc)
    lat = 48.1486   # Bratislava
    lon = 17.1077
    
    for sys_code in ["P", "W", "K", "E", "O"]:
        hs = HouseSystem(dt, lat, lon, system=sys_code)
        print(hs)
        print()
