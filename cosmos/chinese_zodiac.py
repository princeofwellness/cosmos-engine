"""
Chinese Zodiac / Ba Zi (Four Pillars of Destiny) Engine — MIT licensed.

Calculates Four Pillars, animal signs, elements, compatibility, and element balance.
No external dependencies beyond Python stdlib.
"""

import math
from datetime import datetime, timezone
from typing import Optional

# === HEAVENLY STEMS (10) ===
HEAVENLY_STEMS = [
    {"name": "Jia", "chinese": "甲", "element": "Wood", "polarity": "Yang"},
    {"name": "Yi", "chinese": "乙", "element": "Wood", "polarity": "Yin"},
    {"name": "Bing", "chinese": "丙", "element": "Fire", "polarity": "Yang"},
    {"name": "Ding", "chinese": "丁", "element": "Fire", "polarity": "Yin"},
    {"name": "Wu", "chinese": "戊", "element": "Earth", "polarity": "Yang"},
    {"name": "Ji", "chinese": "己", "element": "Earth", "polarity": "Yin"},
    {"name": "Geng", "chinese": "庚", "element": "Metal", "polarity": "Yang"},
    {"name": "Xin", "chinese": "辛", "element": "Metal", "polarity": "Yin"},
    {"name": "Ren", "chinese": "壬", "element": "Water", "polarity": "Yang"},
    {"name": "Gui", "chinese": "癸", "element": "Water", "polarity": "Yin"},
]

# === EARTHLY BRANCHES (12) ===
EARTHLY_BRANCHES = [
    {"name": "Rat", "chinese": "子", "element": "Water", "season": "Winter", "hours": "23-01", "trine": "Dragon/Monkey", "opposite": "Horse"},
    {"name": "Ox", "chinese": "丑", "element": "Earth", "season": "Winter", "hours": "01-03", "trine": "Snake/Rooster", "opposite": "Goat"},
    {"name": "Tiger", "chinese": "寅", "element": "Wood", "season": "Spring", "hours": "03-05", "trine": "Horse/Dog", "opposite": "Monkey"},
    {"name": "Rabbit", "chinese": "卯", "element": "Wood", "season": "Spring", "hours": "05-07", "trine": "Goat/Pig", "opposite": "Rooster"},
    {"name": "Dragon", "chinese": "辰", "element": "Earth", "season": "Spring", "hours": "07-09", "trine": "Rat/Monkey", "opposite": "Dog"},
    {"name": "Snake", "chinese": "巳", "element": "Fire", "season": "Summer", "hours": "09-11", "trine": "Ox/Rooster", "opposite": "Pig"},
    {"name": "Horse", "chinese": "午", "element": "Fire", "season": "Summer", "hours": "11-13", "trine": "Tiger/Dog", "opposite": "Rat"},
    {"name": "Goat", "chinese": "未", "element": "Earth", "season": "Summer", "hours": "13-15", "trine": "Rabbit/Pig", "opposite": "Ox"},
    {"name": "Monkey", "chinese": "申", "element": "Metal", "season": "Autumn", "hours": "15-17", "trine": "Rat/Dragon", "opposite": "Tiger"},
    {"name": "Rooster", "chinese": "酉", "element": "Metal", "season": "Autumn", "hours": "17-19", "trine": "Ox/Snake", "opposite": "Rabbit"},
    {"name": "Dog", "chinese": "戌", "element": "Earth", "season": "Autumn", "hours": "19-21", "trine": "Tiger/Horse", "opposite": "Dragon"},
    {"name": "Pig", "chinese": "亥", "element": "Water", "season": "Winter", "hours": "21-23", "trine": "Rabbit/Goat", "opposite": "Snake"},
]

# === FIVE ELEMENTS ===
FIVE_ELEMENTS = ["Wood", "Fire", "Earth", "Metal", "Water"]

# Generation cycle: feeds the next
ELEMENT_GENERATES = {"Wood": "Fire", "Fire": "Earth", "Earth": "Metal", "Metal": "Water", "Water": "Wood"}

# Control cycle: controls every other element
ELEMENT_CONTROLS = {"Wood": "Earth", "Earth": "Water", "Water": "Fire", "Fire": "Metal", "Metal": "Wood"}

# === ANIMAL TRAITS ===
ANIMAL_TRAITS = {
    "Rat": "Quick-witted, resourceful, versatile, kind. Natural charm and sharp intuition.",
    "Ox": "Diligent, dependable, strong, determined. Patience and hard work define you.",
    "Tiger": "Brave, confident, competitive, unpredictable. Born leader with magnetic presence.",
    "Rabbit": "Gentle, elegant, compassionate, alert. Grace under pressure.",
    "Dragon": "Confident, intelligent, enthusiastic, ambitious. Natural-born leader with cosmic fire.",
    "Snake": "Wise, enigmatic, intuitive, graceful. Deep thinker with strategic mind.",
    "Horse": "Energetic, independent, free-spirited, warm-hearted. Cannot be tamed.",
    "Goat": "Creative, gentle, compassionate, resilient. Artistic soul with quiet strength.",
    "Monkey": "Witty, intelligent, innovative, mischievous. Master problem-solver.",
    "Rooster": "Observant, hardworking, courageous, outspoken. Early riser with sharp eye.",
    "Dog": "Loyal, honest, faithful, protective. The most trustworthy of all signs.",
    "Pig": "Generous, compassionate, diligent, sincere. Pure heart with abundant spirit.",
}

# === MONTH PILLAR LOOKUP ===
# For each year stem, the month stem offset. Month branches are fixed by solar terms.
# Month branch 0 = Tiger (Feb), 1 = Rabbit (Mar), ... 11 = Ox (Jan)
MONTH_STEM_OFFSETS = {
    0: [2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3],  # Year stem: Jia/Ji
    1: [2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3],  # Ji
    2: [4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5],  # Bing/Xin
    3: [4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5],  # Xin
    4: [6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7],  # Wu/Gui
    5: [6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7],  # Gui
    6: [8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9],  # Geng
    7: [8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9],  # Geng
    8: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1],  # Ren
    9: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1],  # Ren
}

# Month branch index by Gregorian month (approximate solar terms ~4th-8th)
# Jan → Ox(1), Feb → Tiger(2), Mar → Rabbit(3), ..., Dec → Rat(0)
MONTH_BRANCH_MAP = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0]

# === HOUR PILLAR LOOKUP ===
# Hour branch = (hour + 1) // 2 % 12
# Hour stem offsets based on day stem
HOUR_STEM_OFFSETS = {
    0: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1],  # Day stem: Jia/Ji
    1: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1],  # Ji
    2: [2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3],  # Bing/Xin
    3: [2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3],  # Xin
    4: [4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5],  # Wu/Gui
    5: [4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5],  # Gui
    6: [6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7],  # Geng
    7: [6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7],  # Geng
    8: [8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9],  # Ren
    9: [8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9],  # Ren
}


class Pillar:
    """A single pillar with stem and branch."""
    def __init__(self, stem_idx: int, branch_idx: int):
        self.stem = HEAVENLY_STEMS[stem_idx % 10]
        self.branch = EARTHLY_BRANCHES[branch_idx % 12]
        self.stem_idx = stem_idx % 10
        self.branch_idx = branch_idx % 12

    def to_dict(self) -> dict:
        return {
            "stem": self.stem["name"],
            "stem_chinese": self.stem["chinese"],
            "stem_element": self.stem["element"],
            "stem_polarity": self.stem["polarity"],
            "branch": self.branch["name"],
            "branch_chinese": self.branch["chinese"],
            "branch_element": self.branch["element"],
            "branch_animal": self.branch["name"],
        }

    def __repr__(self):
        return f"{self.stem['name']}{self.branch['name']} ({self.stem['element']}/{self.branch['element']})"


class ChineseZodiacProfile:
    """Complete Chinese Zodiac / Ba Zi profile."""

    def __init__(self, dt: datetime):
        """
        Args:
            dt: Birth datetime (should be timezone-aware or UTC)
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        self.dt = dt
        self.jd = self._julian_day(dt)
        self._calculate()

    @staticmethod
    def _julian_day(dt: datetime) -> float:
        """Convert datetime to Julian Day Number."""
        y, m, d = dt.year, dt.month, dt.day
        h = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
        if m <= 2:
            y -= 1
            m += 12
        A = y // 100
        B = 2 - A + A // 4
        jd = math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + B - 1524.5
        return jd + h / 24.0

    def _calculate(self):
        y, m, d, h = self.dt.year, self.dt.month, self.dt.day, self.dt.hour

        # === YEAR PILLAR ===
        # Sexagenary cycle: (year - 4) % 60
        year_cycle = (y - 4) % 60
        self.year_pillar = Pillar(year_cycle % 10, year_cycle % 12)
        self.animal = self.year_pillar.branch  # Primary animal sign

        # === MONTH PILLAR ===
        # Month branch is fixed by solar terms (approx by Gregorian month)
        month_branch = MONTH_BRANCH_MAP[m - 1]
        # Month stem depends on year stem
        yr_stem_group = self.year_pillar.stem_idx % 5
        yr_stem = self.year_pillar.stem_idx
        month_stem = MONTH_STEM_OFFSETS[yr_stem][month_branch]
        self.month_pillar = Pillar(month_stem, month_branch)

        # === DAY PILLAR ===
        # Day stem/branch from Julian Day
        day_cycle = int(math.floor(self.jd + 0.5 + 15)) % 60
        self.day_pillar = Pillar(day_cycle % 10, day_cycle % 12)

        # === HOUR PILLAR ===
        # Hour branch = (h+1)//2 % 12
        hour_branch = (h + 1) // 2 % 12
        # Hour stem depends on day stem
        day_stem_group = self.day_pillar.stem_idx % 5
        day_stem = self.day_pillar.stem_idx
        hour_stem = HOUR_STEM_OFFSETS[day_stem][hour_branch]
        self.hour_pillar = Pillar(hour_stem, hour_branch)

        # === ELEMENT ANALYSIS ===
        self._analyze_elements()

        # === LUCKY ELEMENTS ===
        self._find_lucky_elements()

        # === COMPATIBILITY ===
        self._compute_compatibility()

    def _analyze_elements(self):
        """Count elements across all 8 characters (4 stems + 4 branches)."""
        self.element_counts = {e: 0 for e in FIVE_ELEMENTS}
        for pillar in [self.year_pillar, self.month_pillar, self.day_pillar, self.hour_pillar]:
            self.element_counts[pillar.stem["element"]] += 1
            self.element_counts[pillar.branch["element"]] += 1

        self.dominant_element = max(self.element_counts, key=self.element_counts.get)
        missing = [e for e in FIVE_ELEMENTS if self.element_counts[e] == 0]
        weak = [e for e in FIVE_ELEMENTS if self.element_counts[e] == 1]
        self.missing_elements = missing
        self.weak_elements = weak

    def _find_lucky_elements(self):
        """Determine lucky elements based on what's missing/weak."""
        self.lucky_elements = []
        day_element = self.day_pillar.stem["element"]  # Day Master

        if self.missing_elements:
            for elem in self.missing_elements:
                self.lucky_elements.append(elem)
        for elem in self.weak_elements:
            if elem not in self.lucky_elements:
                self.lucky_elements.append(elem)

        # Also add the generation element for the day master
        for giver, receiver in ELEMENT_GENERATES.items():
            if receiver == day_element and giver not in self.lucky_elements:
                if self.element_counts[giver] < 2:
                    self.lucky_elements.append(giver)

    def _compute_compatibility(self):
        """Compute compatibility with all 12 animals."""
        animal_name = self.animal["name"]
        trine = self.animal["trine"].split("/")
        opposite = self.animal["opposite"]

        self.compatibility = []
        for branch in EARTHLY_BRANCHES:
            name = branch["name"]
            if name == animal_name:
                level = "self"
            elif name in trine:
                level = "most_compatible"
            elif name == opposite:
                level = "challenging"
            else:
                level = "neutral"
            self.compatibility.append({"animal": name, "level": level})

    def to_dict(self) -> dict:
        """Export complete profile as dictionary."""
        return {
            "birth_datetime": self.dt.isoformat(),
            "animal": {
                "name": self.animal["name"],
                "chinese": self.animal["chinese"],
                "element": self.animal["element"],
                "traits": ANIMAL_TRAITS.get(self.animal["name"], ""),
                "season": self.animal["season"],
                "trine": self.animal["trine"],
                "opposite": self.animal["opposite"],
            },
            "four_pillars": {
                "year": self.year_pillar.to_dict(),
                "month": self.month_pillar.to_dict(),
                "day": self.day_pillar.to_dict(),
                "hour": self.hour_pillar.to_dict(),
            },
            "day_master": {
                "stem": self.day_pillar.stem["name"],
                "element": self.day_pillar.stem["element"],
                "polarity": self.day_pillar.stem["polarity"],
                "description": f"Day Master is {self.day_pillar.stem['name']} "
                               f"({self.day_pillar.stem['element']} {self.day_pillar.stem['polarity']}). "
                               f"This represents your core self, personality, and life direction."
            },
            "element_balance": {
                "counts": self.element_counts,
                "dominant": self.dominant_element,
                "missing": self.missing_elements,
                "weak": self.weak_elements,
                "lucky": self.lucky_elements,
            },
            "compatibility": self.compatibility,
            "current_year_animal": None,  # Can be populated externally
        }

    def __repr__(self):
        lines = [
            f"Chinese Zodiac: {self.animal['name']} ({self.animal['element']})",
            f"  Year:  {self.year_pillar}",
            f"  Month: {self.month_pillar}",
            f"  Day:   {self.day_pillar}",
            f"  Hour:  {self.hour_pillar}",
            f"  Day Master: {self.day_pillar.stem['name']} ({self.day_pillar.stem['element']})",
            f"  Elements: {self.element_counts}",
            f"  Lucky: {self.lucky_elements}",
        ]
        return "\n".join(lines)


# Quick test
if __name__ == "__main__":
    dt = datetime(1997, 2, 19, 10, 9, 0, tzinfo=timezone.utc)
    cz = ChineseZodiacProfile(dt)
    print(cz)
    import json
    print(json.dumps(cz.to_dict(), indent=2))
