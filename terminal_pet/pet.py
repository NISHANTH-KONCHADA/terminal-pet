"""Core logic for the Terminal Pet.

The pet's state is stored as a small JSON file in the user's home
directory (~/.terminal_pet/state.json). Stats like hunger and happiness
are *computed* from timestamps rather than constantly updated in the
background -- this keeps things simple: no daemons, no cron jobs.
"""

import json
from pathlib import Path
from datetime import datetime, date, timedelta

STATE_DIR = Path.home() / ".terminal_pet"
STATE_FILE = STATE_DIR / "state.json"

# How fast hunger drains, in points per hour since the last commit.
HUNGER_DECAY_PER_HOUR = 4

# Bonus happiness points per day of active commit streak (capped).
MAX_STREAK_HAPPINESS_BONUS = 20

DEFAULT_STATE = {
    "name": "Buddy",
    "created_at": None,
    "last_fed": None,           # ISO timestamp of the last commit/feed
    "last_commit_date": None,   # ISO date string, used for streaks
    "total_commits": 0,
    "current_streak": 0,
    "longest_streak": 0,
    "pets_today": 0,            # how many times you've "petted" the pet today
    "pets_today_date": None,
}


class Pet:
    """Represents the user's virtual coding pet."""

    def __init__(self):
        self.state = self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _load(self):
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                data = json.load(f)
            merged = DEFAULT_STATE.copy()
            merged.update(data)
            return merged
        return None

    def exists(self):
        return self.state is not None

    def save(self):
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=2)

    def create(self, name="Buddy"):
        now = datetime.now()
        self.state = DEFAULT_STATE.copy()
        self.state["name"] = name
        self.state["created_at"] = now.isoformat()
        self.state["last_fed"] = now.isoformat()
        self.save()

    # ------------------------------------------------------------------
    # Computed stats (derived from timestamps, never stored directly)
    # ------------------------------------------------------------------
    def hours_since_fed(self):
        last_fed = datetime.fromisoformat(self.state["last_fed"])
        delta = datetime.now() - last_fed
        return max(0.0, delta.total_seconds() / 3600)

    def hunger(self):
        """0 (starving) to 100 (full). Drains over time since last commit."""
        decayed = self.hours_since_fed() * HUNGER_DECAY_PER_HOUR
        return max(0, round(100 - decayed))

    def happiness(self):
        """0 to 100. Based on hunger, with a bonus for active streaks."""
        hunger = self.hunger()
        streak_bonus = min(self.state["current_streak"] * 2, MAX_STREAK_HAPPINESS_BONUS)
        return max(0, min(100, hunger + streak_bonus))

    def stage(self):
        """The pet's evolution stage, based on total commits fed to it."""
        commits = self.state["total_commits"]
        if commits == 0:
            return "egg"
        elif commits < 5:
            return "hatchling"
        elif commits < 20:
            return "sprout"
        elif commits < 50:
            return "adult"
        else:
            return "legendary"

    def mood(self):
        """A simple mood label used to pick ASCII art and messages."""
        hunger = self.hunger()
        happiness = self.happiness()

        if self.stage() == "egg":
            return "egg"
        if hunger <= 10:
            return "starving"
        if hunger < 35:
            return "hungry"
        if happiness >= 80:
            return "thriving"
        return "content"

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def feed(self):
        """Called when a commit happens. Refills hunger and updates streaks."""
        now = datetime.now()
        today = now.date()

        last_commit_date = self.state["last_commit_date"]
        if last_commit_date:
            last_date = date.fromisoformat(last_commit_date)
            gap = (today - last_date).days
            if gap == 0:
                pass  # already committed today, streak unchanged
            elif gap == 1:
                self.state["current_streak"] += 1
            else:
                self.state["current_streak"] = 1
        else:
            self.state["current_streak"] = 1

        self.state["longest_streak"] = max(
            self.state["longest_streak"], self.state["current_streak"]
        )
        self.state["last_commit_date"] = today.isoformat()
        self.state["last_fed"] = now.isoformat()
        self.state["total_commits"] += 1
        self.save()

    def pet(self):
        """A small, limited daily happiness boost from interacting directly.

        Returns True if the pet was successfully petted, False if the
        daily limit (3) has already been reached.
        """
        today = date.today().isoformat()
        if self.state["pets_today_date"] != today:
            self.state["pets_today_date"] = today
            self.state["pets_today"] = 0

        if self.state["pets_today"] >= 3:
            return False

        self.state["pets_today"] += 1
        # A pet nudges the "last_fed" clock forward a bit, which gives
        # a small, temporary hunger/happiness boost.
        last_fed = datetime.fromisoformat(self.state["last_fed"])
        nudged = last_fed + timedelta(minutes=30)
        if nudged > datetime.now():
            nudged = datetime.now()
        self.state["last_fed"] = nudged.isoformat()
        self.save()
        return True
