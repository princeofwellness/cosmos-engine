"""
Complete astrological constants — planets, signs, houses, aspects,
elements, modalities, dignities, and human design gates.

All data derived from standard astrological references. Public domain.
"""

# === Planets (Traditional + Modern + Astrological Points) ===

PLANETS = {
    "SUN":       {"id": 0,  "name": "Sun",       "symbol": "☉", "orb": 15.0},
    "MOON":      {"id": 1,  "name": "Moon",      "symbol": "☽", "orb": 12.0},
    "MERCURY":   {"id": 2,  "name": "Mercury",   "symbol": "☿", "orb": 7.0},
    "VENUS":     {"id": 3,  "name": "Venus",     "symbol": "♀", "orb": 7.0},
    "MARS":      {"id": 4,  "name": "Mars",      "symbol": "♂", "orb": 8.0},
    "JUPITER":   {"id": 5,  "name": "Jupiter",   "symbol": "♃", "orb": 9.0},
    "SATURN":    {"id": 6,  "name": "Saturn",    "symbol": "♄", "orb": 9.0},
    "URANUS":    {"id": 7,  "name": "Uranus",    "symbol": "♅", "orb": 5.0},
    "NEPTUNE":   {"id": 8,  "name": "Neptune",   "symbol": "♆", "orb": 5.0},
    "PLUTO":     {"id": 9,  "name": "Pluto",     "symbol": "♇", "orb": 5.0},
    "CHIRON":    {"id": 10, "name": "Chiron",    "symbol": "⚷", "orb": 3.0},
    "NORTH_NODE":{"id": 11, "name": "North Node","symbol": "☊", "orb": 3.0},
    "SOUTH_NODE":{"id": 12, "name": "South Node","symbol": "☋", "orb": 3.0},
    "ASC":       {"id": 13, "name": "Ascendant", "symbol": "ASC", "orb": 5.0},
    "MC":        {"id": 14, "name": "Midheaven", "symbol": "MC", "orb": 5.0},
    "LILITH":    {"id": 15, "name": "Lilith",    "symbol": "⚸", "orb": 3.0},
    "CERES":     {"id": 16, "name": "Ceres",     "symbol": "⚳", "orb": 3.0},
    "PALLAS":    {"id": 17, "name": "Pallas",    "symbol": "⚴", "orb": 3.0},
    "JUNO":      {"id": 18, "name": "Juno",      "symbol": "⚵", "orb": 3.0},
    "VESTA":     {"id": 19, "name": "Vesta",     "symbol": "⚶", "orb": 3.0},
}

# Map to Skyfield body names
SKYFIELD_PLANETS = {
    "SUN": "sun",
    "MOON": "moon",
    "MERCURY": "mercury",
    "VENUS": "venus",
    "MARS": "mars",
    "JUPITER": "jupiter barycenter",
    "SATURN": "saturn barycenter",
    "URANUS": "uranus barycenter",
    "NEPTUNE": "neptune barycenter",
    "PLUTO": "pluto barycenter",
}

# === Zodiac Signs ===

SIGNS = {
    1:  {"name": "Aries",       "symbol": "♈", "element": "Fire",      "modality": "Cardinal", "ruler": "MARS",      "start": 0.0},
    2:  {"name": "Taurus",      "symbol": "♉", "element": "Earth",     "modality": "Fixed",    "ruler": "VENUS",     "start": 30.0},
    3:  {"name": "Gemini",      "symbol": "♊", "element": "Air",       "modality": "Mutable",  "ruler": "MERCURY",   "start": 60.0},
    4:  {"name": "Cancer",      "symbol": "♋", "element": "Water",     "modality": "Cardinal", "ruler": "MOON",      "start": 90.0},
    5:  {"name": "Leo",         "symbol": "♌", "element": "Fire",      "modality": "Fixed",    "ruler": "SUN",       "start": 120.0},
    6:  {"name": "Virgo",       "symbol": "♍", "element": "Earth",     "modality": "Mutable",  "ruler": "MERCURY",   "start": 150.0},
    7:  {"name": "Libra",        "symbol": "♎", "element": "Air",       "modality": "Cardinal", "ruler": "VENUS",     "start": 180.0},
    8:  {"name": "Scorpio",      "symbol": "♏", "element": "Water",     "modality": "Fixed",    "ruler": "PLUTO",     "start": 210.0},
    9:  {"name": "Sagittarius",  "symbol": "♐", "element": "Fire",      "modality": "Mutable",  "ruler": "JUPITER",   "start": 240.0},
    10: {"name": "Capricorn",    "symbol": "♑", "element": "Earth",     "modality": "Cardinal", "ruler": "SATURN",    "start": 270.0},
    11: {"name": "Aquarius",     "symbol": "♒", "element": "Air",       "modality": "Fixed",    "ruler": "URANUS",    "start": 300.0},
    12: {"name": "Pisces",       "symbol": "♓", "element": "Water",     "modality": "Mutable",  "ruler": "NEPTUNE",   "start": 330.0},
}

ELEMENTS = ["Fire", "Earth", "Air", "Water"]
MODALITIES = ["Cardinal", "Fixed", "Mutable"]

# === Aspects ===

ASPECTS = {
    "conjunction": {"angle": 0.0,    "orb": 8.0,  "symbol": "☌", "nature": "neutral"},
    "semisextile": {"angle": 30.0,   "orb": 2.0,  "symbol": "⚺", "nature": "minor"},
    "semisquare":  {"angle": 45.0,   "orb": 3.0,  "symbol": "∠", "nature": "minor"},
    "sextile":     {"angle": 60.0,   "orb": 6.0,  "symbol": "⚹", "nature": "harmonious"},
    "quintile":    {"angle": 72.0,   "orb": 2.0,  "symbol": "Q",  "nature": "creative"},
    "square":      {"angle": 90.0,   "orb": 8.0,  "symbol": "□", "nature": "challenging"},
    "trine":       {"angle": 120.0,  "orb": 8.0,  "symbol": "△", "nature": "harmonious"},
    "sesquiquadrate":{"angle": 135.0,"orb": 3.0,  "symbol": "⚼", "nature": "minor"},
    "biquintile":  {"angle": 144.0,  "orb": 2.0,  "symbol": "bQ", "nature": "creative"},
    "quincunx":    {"angle": 150.0,  "orb": 5.0,  "symbol": "⚻", "nature": "adjustment"},
    "opposition":  {"angle": 180.0,  "orb": 8.0,  "symbol": "☍", "nature": "challenging"},
}

# === House Systems ===

HOUSE_SYSTEMS = {
    "P": "Placidus",
    "W": "Whole Sign",
    "K": "Koch",
    "E": "Equal House",
    "C": "Campanus",
    "R": "Regiomontanus",
    "O": "Porphyry",
}

# === Dignities (Essential) ===

# Rulership: each sign's ruler
RULERSHIP = {s: SIGNS[s]["ruler"] for s in SIGNS}

# Detriment: opposite of rulership
DETRIMENT = {
    "SUN":    "SATURN",
    "MOON":   "SATURN",
    "MERCURY": "JUPITER",
    "VENUS":   "MARS",
    "MARS":    "VENUS",
    "JUPITER": "MERCURY",
    "SATURN":  "MOON",
    "URANUS":  "SUN",
    "NEPTUNE": "MERCURY",
    "PLUTO":   "VENUS",
}

# Exaltation: planet's exaltation sign
EXALTATION = {
    "SUN":    1,   # Aries 19°
    "MOON":   2,   # Taurus 3°
    "MERCURY": 6,  # Virgo 15°
    "VENUS":  12,  # Pisces 27°
    "MARS":   10,  # Capricorn 28°
    "JUPITER": 4,  # Cancer 15°
    "SATURN": 7,   # Libra 21°
    "URANUS": 8,   # Scorpio
    "NEPTUNE": 4,  # Cancer
    "PLUTO":   5,  # Leo
}

# Fall: opposite of exaltation
FALL_SIGN = {p: ((EXALTATION[p] + 5) % 12) + 1 for p in EXALTATION}

# === Human Design Gate Data ===

# Gate to sign-degree mapping (tropical zodiac, 0° Aries = Gate 41)
# Gates 1-64, each occupies 5.625° of the zodiac (360/64)
GATE_DEGREES = {}
for gate in range(1, 65):
    start_deg = (gate - 41) * 5.625
    if start_deg < 0:
        start_deg += 360.0
    GATE_DEGREES[gate] = start_deg % 360.0

# Gate line mapping (each gate has 6 lines, each 0.9375°)
GATE_LINE_DEGREE = 5.625 / 6  # 0.9375°
