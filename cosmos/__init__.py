"""
Cosmos Engine — MIT-licensed astrological computation engine.

Zero dependency on Swiss Ephemeris. Uses JPL ephemerides via Skyfield
for planetary positions (public domain NASA data). All astrological
calculations (houses, aspects, dignities) implemented from scratch.

Commercial use: fully allowed under MIT license.
"""

__version__ = "1.0.0"

from .chart import Chart
from .planets import PlanetPositions
from .houses import HouseSystem
from .aspects import AspectEngine
from .constants import (
    PLANETS, SIGNS, HOUSE_SYSTEMS, ASPECTS, 
    ELEMENTS, MODALITIES, RULERSHIP, EXALTATION, DETRIMENT, FALL_SIGN,
)

__all__ = [
    "Chart",
    "PlanetPositions",
    "HouseSystem",
    "AspectEngine",
    "PLANETS", "SIGNS", "HOUSE_SYSTEMS", "ASPECTS",
    "ELEMENTS", "MODALITIES",
]
