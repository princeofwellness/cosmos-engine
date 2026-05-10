"""
Pythagorean Numerology Engine — MIT licensed.

Calculates all major numerology numbers from name and birth date.
No external dependencies beyond Python stdlib.
"""

from datetime import datetime
from typing import Optional

# === LETTER-TO-NUMBER MAPPING (Pythagorean) ===
LETTER_MAP = {
    'A':1,'B':2,'C':3,'D':4,'E':5,'F':6,'G':7,'H':8,'I':9,
    'J':1,'K':2,'L':3,'M':4,'N':5,'O':6,'P':7,'Q':8,'R':9,
    'S':1,'T':2,'U':3,'V':4,'W':5,'X':6,'Y':7,'Z':8,
}

VOWELS = set('AEIOU')
KARMIC_DEBTS = {13, 14, 16, 19}

# === NUMBER MEANINGS ===
NUMBER_MEANINGS = {
    1:  "The Leader — independent, ambitious, original, pioneering. You carve your own path.",
    2:  "The Diplomat — sensitive, cooperative, intuitive, peacemaker. You thrive in partnership.",
    3:  "The Creator — expressive, joyful, charismatic, artistic. Communication is your gift.",
    4:  "The Builder — practical, disciplined, stable, hardworking. You build lasting foundations.",
    5:  "The Adventurer — freedom-loving, versatile, curious, progressive. Change is your fuel.",
    6:  "The Nurturer — responsible, loving, harmonious, healer. You serve through care.",
    7:  "The Seeker — spiritual, analytical, introspective, wise. Truth is your compass.",
    8:  "The Powerhouse — ambitious, authoritative, abundant, material mastery. You manifest wealth.",
    9:  "The Humanitarian — compassionate, wise, completion, universal love. You serve the world.",
    11: "The Master Intuitive — illumination, spiritual messenger, inspired visionary. Higher channel.",
    22: "The Master Builder — manifest dreams into reality, large-scale achievement, ancient wisdom.",
    33: "The Master Teacher — unconditional love, selfless service, spiritual nurturing of humanity.",
}

KARMIC_MEANINGS = {
    13: "Karmic Debt 13 — Past misuse of communication/laziness. Must learn discipline and hard work.",
    14: "Karmic Debt 14 — Past abuse of freedom. Must learn moderation and commitment.",
    16: "Karmic Debt 16 — Past misuse of love/ego. Must learn humility and rebuild from zero.",
    19: "Karmic Debt 19 — Past abuse of power. Must learn independence without dominating others.",
}


def reduce_number(n: int, preserve_master: bool = True) -> int:
    """Reduce a number to a single digit, preserving master numbers 11,22,33 if requested."""
    while n > 9:
        if preserve_master and n in (11, 22, 33):
            return n
        n = sum(int(d) for d in str(n))
    return n


def _name_value(name: str) -> int:
    """Calculate the numerical value of a name."""
    return sum(LETTER_MAP.get(c.upper(), 0) for c in name if c.isalpha())


def _name_vowel_value(name: str) -> int:
    """Calculate the numerical value of vowels in a name."""
    return sum(LETTER_MAP.get(c.upper(), 0) for c in name if c.upper() in VOWELS)


def _name_consonant_value(name: str) -> int:
    """Calculate the numerical value of consonants in a name."""
    return sum(LETTER_MAP.get(c.upper(), 0) for c in name if c.isalpha() and c.upper() not in VOWELS)


class NumerologyProfile:
    """Complete numerology profile from name and birth date."""

    def __init__(self, name: str, birth_date_str: str):
        """
        Args:
            name: Full birth name (e.g. "John Michael Doe")
            birth_date_str: Birth date in YYYY-MM-DD format
        """
        self.name = name.strip().upper()
        self.name_parts = [p for p in self.name.split() if p]
        self.birth_date = datetime.strptime(birth_date_str.strip(), "%Y-%m-%d")
        self._calculate()

    def _calculate(self):
        """Compute all numerology numbers."""
        y, m, d = self.birth_date.year, self.birth_date.month, self.birth_date.day

        # === Core Numbers ===
        # Life Path: sum of all birth date digits
        lp_raw = sum(int(c) for c in f"{y}{m:02d}{d:02d}")
        self.life_path = reduce_number(lp_raw)
        self._life_path_raw = lp_raw

        # Destiny/Expression: sum of all name letters
        dest_parts = [_name_value(p) for p in self.name_parts]
        dest_raw = sum(reduce_number(p, False) for p in dest_parts)
        self.destiny = reduce_number(dest_raw)
        self._destiny_parts = [reduce_number(p, False) for p in dest_parts]
        self._destiny_raw = dest_raw

        # Soul Urge / Heart's Desire: vowels only
        soul_parts = [_name_vowel_value(p) for p in self.name_parts]
        soul_raw = sum(reduce_number(p, False) for p in soul_parts)
        self.soul_urge = reduce_number(soul_raw) if soul_raw > 0 else reduce_number(dest_raw)

        # Personality: consonants only
        pers_parts = [_name_consonant_value(p) for p in self.name_parts]
        pers_raw = sum(reduce_number(p, False) for p in pers_parts)
        self.personality = reduce_number(pers_raw)

        # Birthday Number: day of birth
        self.birthday = d if d <= 31 else reduce_number(d)

        # Maturity Number: Life Path + Destiny
        self.maturity = reduce_number(self.life_path + self.destiny)

        # Balance Number: initials only
        initials = ''.join(p[0] for p in self.name_parts if p)
        bal_raw = _name_value(initials)
        self.balance = reduce_number(bal_raw)

        # === Karmic Debt Detection ===
        self.karmic_debts = []
        for label, val in [("Life Path", lp_raw), ("Destiny", dest_raw),
                           ("Soul Urge", soul_raw), ("Personality", pers_raw)]:
            if val in KARMIC_DEBTS:
                self.karmic_debts.append({"number": val, "source": label})

        # === Challenge Numbers (4 life challenges) ===
        # Challenge 1: |month - day|
        self.challenge_1 = abs(reduce_number(m, False) - reduce_number(d, False)) or 1
        # Challenge 2: |day - year_reduced|
        yr = reduce_number(y, False)
        self.challenge_2 = abs(reduce_number(d, False) - yr) or 1
        # Challenge 3: |Challenge1 - Challenge2|
        self.challenge_3 = abs(self.challenge_1 - self.challenge_2) or 1
        # Challenge 4: |month - year_reduced|
        self.challenge_4 = abs(reduce_number(m, False) - yr) or 1

        # === Pinnacle Numbers (4 life phases) ===
        # Pinnacle 1 (0-36 years): month + day
        self.pinnacle_1 = reduce_number(reduce_number(m, False) + reduce_number(d, False))
        # Pinnacle 2 (36-45 years): day + year_reduced
        self.pinnacle_2 = reduce_number(reduce_number(d, False) + yr)
        # Pinnacle 3 (45-54 years): Pinnacle1 + Pinnacle2
        self.pinnacle_3 = reduce_number(self.pinnacle_1 + self.pinnacle_2)
        # Pinnacle 4 (54+ years): month + year_reduced
        self.pinnacle_4 = reduce_number(reduce_number(m, False) + yr)

    def to_dict(self) -> dict:
        """Export complete profile as a dictionary."""
        return {
            "name": self.name,
            "birth_date": self.birth_date.strftime("%Y-%m-%d"),
            "core": {
                "life_path": {"number": self.life_path, "raw": self._life_path_raw,
                              "meaning": NUMBER_MEANINGS.get(self.life_path, "")},
                "destiny": {"number": self.destiny, "parts": self._destiny_parts,
                            "meaning": NUMBER_MEANINGS.get(self.destiny, "")},
                "soul_urge": {"number": self.soul_urge,
                              "meaning": NUMBER_MEANINGS.get(self.soul_urge, "")},
                "personality": {"number": self.personality,
                                "meaning": NUMBER_MEANINGS.get(self.personality, "")},
                "birthday": {"number": self.birthday},
                "maturity": {"number": self.maturity,
                             "meaning": NUMBER_MEANINGS.get(self.maturity, "")},
                "balance": {"number": self.balance,
                            "meaning": NUMBER_MEANINGS.get(self.balance, "")},
            },
            "karmic_debts": [{"number": k["number"], "source": k["source"],
                              "meaning": KARMIC_MEANINGS.get(k["number"], "")}
                             for k in self.karmic_debts],
            "challenges": {
                "first": self.challenge_1,
                "second": self.challenge_2,
                "third": self.challenge_3,
                "fourth": self.challenge_4,
            },
            "pinnacles": {
                "first": self.pinnacle_1,
                "second": self.pinnacle_2,
                "third": self.pinnacle_3,
                "fourth": self.pinnacle_4,
            },
            "master_numbers": {str(n): NUMBER_MEANINGS[n] for n in [11, 22, 33]
                               if n in [self.life_path, self.destiny, self.soul_urge,
                                        self.personality, self.maturity, self.balance]},
        }

    def __repr__(self):
        return (f"NumerologyProfile({self.name})\n"
                f"  Life Path: {self.life_path} — {NUMBER_MEANINGS.get(self.life_path, '')}\n"
                f"  Destiny:   {self.destiny} — {NUMBER_MEANINGS.get(self.destiny, '')}\n"
                f"  Soul Urge: {self.soul_urge} — {NUMBER_MEANINGS.get(self.soul_urge, '')}\n"
                f"  Maturity:  {self.maturity}")


# Quick test
if __name__ == "__main__":
    np = NumerologyProfile("John Michael Doe", "1990-06-15")
    print(np)
    import json
    print(json.dumps(np.to_dict(), indent=2))
