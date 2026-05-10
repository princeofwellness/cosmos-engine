"""
POLARIS Synthesis Engine — combines Astrology, Human Design, Numerology, and Chinese Zodiac.

Produces a unified analysis from birth data: name, date, time, location.
MIT licensed. Built on Cosmos Engine foundations.
"""

import json
from datetime import datetime, timezone
from typing import Optional

from .chart import Chart
from .numerology import NumerologyProfile
from .chinese_zodiac import ChineseZodiacProfile


class SynthesisProfile:
    """Complete four-system synthesis profile for one person."""

    def __init__(self, name: str, birth_dt: str, lat: float, lon: float,
                 house_system: str = "P", ephemeris_path: str = "/tmp/hd-research/de421.bsp"):
        """
        Args:
            name: Full birth name
            birth_dt: ISO datetime string (e.g. "1997-02-19T10:09:00+00:00")
            lat: Geographic latitude
            lon: Geographic longitude
        """
        self.name = name
        self.lat = lat
        self.lon = lon

        # Parse datetime
        dt = datetime.fromisoformat(birth_dt)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        self.dt = dt

        # Date string for numerology
        date_str = dt.strftime("%Y-%m-%d")

        # === Calculate all four systems ===
        self.astrology = Chart(dt, lat, lon, house_system=house_system,
                               ephemeris_path=ephemeris_path)
        self.numerology = NumerologyProfile(name, date_str)
        self.chinese_zodiac = ChineseZodiacProfile(dt)

        # HD = embedded in astrology via Chart.hd_gates
        # (HD proper would need pyhd, but gates are computed)

        # === Cross-system synthesis ===
        self._synthesize()

    def _synthesize(self):
        """Compute cross-system correlations and patterns."""
        # Element comparison: Astrology elements vs Chinese Zodiac elements
        astro_elements = self.astrology.element_counts
        cz_elements = self.chinese_zodiac.element_counts

        # Shared dominant patterns
        self.cross_elements = {
            "astrology": astro_elements,
            "chinese_zodiac": cz_elements,
            "shared_strong": [e for e in astro_elements
                              if astro_elements[e] >= 2 and cz_elements.get(e, 0) >= 2],
            "shared_weak": [e for e in astro_elements
                            if astro_elements[e] <= 1 and cz_elements.get(e, 0) <= 1],
        }

        # Life Path correlations
        lp = self.numerology.life_path
        self.life_path_astro = self._lp_astro_correlation(lp)
        self.life_path_cz = self._lp_cz_correlation(lp)

    def _lp_astro_correlation(self, lp: int) -> dict:
        """Correlate Life Path number with astrological patterns."""
        correlations = {
            1: ("Sun/Mars/Aries energy", "Pioneering, leadership, independence"),
            2: ("Moon/Venus energy", "Harmony, partnership, sensitivity"),
            3: ("Mercury/Jupiter energy", "Communication, creativity, expansion"),
            4: ("Saturn/Earth energy", "Structure, discipline, foundations"),
            5: ("Mercury/Uranus energy", "Freedom, versatility, change"),
            6: ("Venus/Moon energy", "Nurturing, harmony, service"),
            7: ("Neptune/Uranus energy", "Spirituality, analysis, mysticism"),
            8: ("Saturn/Pluto energy", "Power, abundance, authority"),
            9: ("Jupiter/Neptune energy", "Humanitarianism, completion, wisdom"),
            11: ("Uranus/Neptune energy", "Illumination, spiritual mastery"),
            22: ("Saturn/Jupiter energy", "Master manifestation, large-scale building"),
            33: ("Neptune/Venus energy", "Master teaching, unconditional love"),
        }
        return {"number": lp, "planetary_correlation": correlations.get(lp, ("", ""))[0],
                "description": correlations.get(lp, ("", ""))[1]}

    def _lp_cz_correlation(self, lp: int) -> dict:
        """Correlate Life Path with Chinese Zodiac element."""
        # Simplified mapping: Life Path → Five Element
        element_map = {
            1: "Water", 2: "Earth", 3: "Wood", 4: "Wood", 5: "Fire",
            6: "Metal", 7: "Metal", 8: "Earth", 9: "Fire",
            11: "Water", 22: "Earth", 33: "Fire",
        }
        elem = element_map.get(lp, "Earth")
        return {"number": lp, "five_element": elem}

    def to_dict(self) -> dict:
        """Export full synthesis profile."""
        return {
            "meta": {
                "name": self.name,
                "birth_datetime": self.dt.isoformat(),
                "lat": self.lat,
                "lon": self.lon,
            },
            "astrology": self.astrology.to_dict(compact=False),
            "numerology": self.numerology.to_dict(),
            "chinese_zodiac": self.chinese_zodiac.to_dict(),
            "cross_synthesis": {
                "elements": self.cross_elements,
                "life_path_astrology": self.life_path_astro,
                "life_path_chinese_zodiac": self.life_path_cz,
            },
        }


def generate_full_html(profile: SynthesisProfile) -> str:
    """Generate a one-page HTML from a synthesis profile.
    
    This is the main output function — produces a complete, styled
    HTML page that the user can view or share.
    """
    a = profile.astrology.to_dict()
    n = profile.numerology.to_dict()
    cz = profile.chinese_zodiac.to_dict()

    # Extract key data
    asc_lon = a["angles"]["ascendant"]
    from .constants import SIGNS
    asc_sign = SIGNS[int(asc_lon / 30) + 1]
    asc_d = int(asc_lon % 30)
    asc_m = int((asc_lon % 30 - asc_d) * 60)

    mc_lon = a["angles"]["midheaven"]
    mc_sign = SIGNS[int(mc_lon / 30) + 1]
    mc_d = int(mc_lon % 30)
    mc_m = int((mc_lon % 30 - mc_d) * 60)

    sun = a["planets"]["SUN"]
    moon = a["planets"]["MOON"]
    sun_sign = sun["sign_info"]["sign_name"]
    moon_sign = moon["sign_info"]["sign_name"]
    sun_deg = int(sun["sign_degree"])
    sun_min = int((sun["sign_degree"] - sun_deg) * 60)
    moon_deg = int(moon["sign_degree"])
    moon_min = int((moon["sign_degree"] - moon_deg) * 60)

    # Return a placeholder for now — full HTML builder in next step
    return "<!-- POLARIS Profile -->"


if __name__ == "__main__":
    import json
    profile = SynthesisProfile(
        name="Test User",
        birth_dt="1997-02-19T10:09:00+00:00",
        lat=48.1486,
        lon=17.1077,
    )
    print(json.dumps(profile.to_dict(), indent=2)[:3000])
