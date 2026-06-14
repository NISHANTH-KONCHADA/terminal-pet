# Build a Terminal Pet That Feeds on Your Git Commits (Python)

You know that feeling when you haven't committed in three days and you just... feel bad about it? Let's turn that feeling into an actual creature that can starve.

In this tutorial, we're building **Terminal Pet** — a tiny virtual pet that lives in `~/.terminal_pet/state.json` and reacts to your coding habits. Commit code, and it gets fed and happy. Ghost your repo for a day, and it starts looking a little rough. Build up a commit streak, and it evolves from a sad little egg into a "Legendary" creature.

By the end, you'll have:

- A real, installable CLI tool (`pet status`, `pet feed`, `pet pet`)
- A `post-commit` git hook that automatically feeds your pet
- A little stat system (hunger, happiness, streaks, evolution stages)
- Some genuinely fun ASCII art reactions

No external libraries. No background processes. Just Python's standard library and a git hook.

> 💡 **Add a screenshot here**: a terminal window showing `pet status` with your pet's ASCII art and stat bars. This is your hero image!

---

## How it's going to work (the big idea)

Before we write any code, let's get the architecture straight — it's simpler than it sounds.

1. **State lives in a JSON file.** `~/.terminal_pet/state.json` stores things like your pet's name, total commits, current streak, and the timestamp of the last time it was fed.
2. **Stats are *computed*, not stored.** Instead of running a background process that ticks down hunger every minute (which would be a nightmare to manage), we calculate hunger on the fly: *"how many hours has it been since the last commit?"* The longer the gap, the hungrier the pet.
3. **A git hook does the feeding.** Every repo where you run `pet init` gets a `post-commit` hook installed. Every `git commit` runs `pet feed` behind the scenes.
4. **Evolution is just a function of total commits.** 0 commits = egg, 5+ = hatchling, 20+ = sprout, and so on.

That's it. No daemons, no cron jobs, no polling. Just timestamps and math.

---

## Prerequisites

- Python 3.8+
- Git installed and a repo you don't mind testing in
- Basic comfort with the terminal and reading Python

---

## Step 1: Set up the project

Let's create the folder structure first:

```bash
mkdir terminal-pet && cd terminal-pet
mkdir terminal_pet
touch terminal_pet/__init__.py
touch terminal_pet/pet.py terminal_pet/art.py terminal_pet/cli.py terminal_pet/hooks.py
touch pyproject.toml README.md
```

You should end up with this structure:

```
terminal-pet/
├── pyproject.toml
├── README.md
└── terminal_pet/
    ├── __init__.py
    ├── pet.py      # the Pet class: state, hunger, streaks
    ├── art.py       # ASCII art and messages
    ├── cli.py        # the `pet` command itself
    └── hooks.py     # installs the git hook
```

In `terminal_pet/__init__.py`, just add a version string so the package has something in it:

```python
"""Terminal Pet -- a virtual pet that lives in your terminal and reacts to your git commits."""

__version__ = "0.1.0"
```

---

## Step 2: The `Pet` class — state and "decay" logic

This is the heart of the whole project. Open `terminal_pet/pet.py`.

### Defining the state

First, let's decide what we actually need to *store* vs. what we can *calculate*.

**Stored** (in `~/.terminal_pet/state.json`):
- `name`, `created_at`
- `last_fed` — timestamp of the last commit
- `last_commit_date` — just the date, used for streak math
- `total_commits`, `current_streak`, `longest_streak`
- `pets_today` / `pets_today_date` — for a daily "petting" limit

**Calculated** (every time you run `pet status`):
- Hunger (based on time since `last_fed`)
- Happiness (based on hunger + streak bonus)
- Mood and evolution stage

This split is the key insight — it means our state file barely changes, but the pet still feels "alive" because its stats shift every time you check on it.

Here's the setup:

```python
import json
from pathlib import Path
from datetime import datetime, date, timedelta

STATE_DIR = Path.home() / ".terminal_pet"
STATE_FILE = STATE_DIR / "state.json"

HUNGER_DECAY_PER_HOUR = 4
MAX_STREAK_HAPPINESS_BONUS = 20

DEFAULT_STATE = {
    "name": "Buddy",
    "created_at": None,
    "last_fed": None,
    "last_commit_date": None,
    "total_commits": 0,
    "current_streak": 0,
    "longest_streak": 0,
    "pets_today": 0,
    "pets_today_date": None,
}
```

We're storing everything in the user's home directory so the pet persists across all your projects — it's *your* pet, not a per-repo thing.

### Loading and saving

```python
class Pet:
    def __init__(self):
        self.state = self._load()

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
```

The `merged = DEFAULT_STATE.copy(); merged.update(data)` trick is a nice habit — if you ever add a new field to `DEFAULT_STATE` later, old save files won't break. They'll just get the new field's default value.

### The hunger calculation (the fun part)

Here's where the "lazy decay" idea comes to life:

```python
    def hours_since_fed(self):
        last_fed = datetime.fromisoformat(self.state["last_fed"])
        delta = datetime.now() - last_fed
        return max(0.0, delta.total_seconds() / 3600)

    def hunger(self):
        """0 (starving) to 100 (full). Drains over time since last commit."""
        decayed = self.hours_since_fed() * HUNGER_DECAY_PER_HOUR
        return max(0, round(100 - decayed))
```

With `HUNGER_DECAY_PER_HOUR = 4`, your pet goes from full (100) to starving (0) in 25 hours — roughly "commit at least once a day or your pet notices."

### Happiness and streak bonuses

Happiness is mostly hunger, but with a little bonus for keeping up a commit streak — so even a slightly-hungry pet can still be happy if you've been consistent:

```python
    def happiness(self):
        """0 to 100. Based on hunger, with a bonus for active streaks."""
        hunger = self.hunger()
        streak_bonus = min(self.state["current_streak"] * 2, MAX_STREAK_HAPPINESS_BONUS)
        return max(0, min(100, hunger + streak_bonus))
```

### Evolution stages

This is just a lookup based on total commits:

```python
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
```

### Mood — tying it all together

Mood is what decides which ASCII art and message we show:

```python
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
```

### Feeding — where commits become pet food

This is called every time you commit. It's also where the streak logic lives:

```python
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
```

Walk through the streak logic with me:

- **Gap of 0 days** (you already committed today) → streak stays the same. No double-dipping.
- **Gap of 1 day** (you committed yesterday, and now today) → streak goes up by one. 🔥
- **Gap of 2+ days** (you took a break) → streak resets to 1.

### A little bonus: petting your pet

Just for fun, let's let users interact with the pet directly — up to 3 times a day, it gives a small temporary hunger boost:

```python
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
        last_fed = datetime.fromisoformat(self.state["last_fed"])
        nudged = last_fed + timedelta(minutes=30)
        if nudged > datetime.now():
            nudged = datetime.now()
        self.state["last_fed"] = nudged.isoformat()
        self.save()
        return True
```

Petting "rewinds" the hunger clock by 30 minutes (capped at "now," so you can't pet your way to a full pet instantly).

That's the entire data layer! Save the file — `pet.py` is done.

---

## Step 3: ASCII art and personality

Now for the part that makes this actually *fun*: `terminal_pet/art.py`.

We'll define ASCII art and flavor messages for each mood. Feel free to get creative here — this is your pet's personality.

```python
import random

ART = {
    "egg": r"""
       ___
     .'   `.
    /  o o  \
   |    >    |
    \  ___  /
     `.___.'
    """,
    "thriving": r"""
     /\_/\
    ( ^.^ )
     > ^ <
    /|   |\
   (_|   |_)
    """,
    "content": r"""
     /\_/\
    ( -.- )
     >   <
    /|   |\
   (_|   |_)
    """,
    "hungry": r"""
     /\_/\
    ( o.o )
     >  <
    /|   |\
   (_|   |_)   ...rumble...
    """,
    "starving": r"""
     /\_/\
    ( x.x )
     >  <
    /|   |\
   (_|   |_)   *weak noises*
    """,
}
```

> 💡 **Try this**: replace these with your own ASCII art! Sites like [asciiart.eu](https://www.asciiart.eu/) have tons of small animal art you can adapt.

Next, give each mood a few possible messages — picking randomly keeps repeated `pet status` checks from feeling stale:

```python
MESSAGES = {
    "egg": [
        "Something's about to hatch... make a commit to find out!",
        "Shh... it's still incubating. Commit some code to wake it up!",
    ],
    "thriving": [
        "Your pet is having the BEST day. Keep up that streak!",
        "Look at that glow! Your pet feels unstoppable.",
        "Your pet is doing little happy laps around your terminal.",
    ],
    "content": [
        "Your pet is feeling pretty good. A commit would make its day!",
        "All is well. Your pet is content, but a fresh commit never hurts.",
    ],
    "hungry": [
        "Your pet's stomach is growling. Maybe it's time to commit something?",
        "It's been a while since your last commit... your pet is getting hungry.",
    ],
    "starving": [
        "Your pet hasn't seen a commit in AGES. It's fading fast!",
        "SOS! Your pet desperately needs you to commit some code.",
    ],
}

STAGE_NAMES = {
    "egg": "Egg",
    "hatchling": "Hatchling",
    "sprout": "Sprout",
    "adult": "Adult",
    "legendary": "Legendary",
}
```

And a few small helper functions, including a simple text progress bar for hunger/happiness:

```python
def get_art(mood):
    return ART.get(mood, ART["content"])


def get_message(mood):
    return random.choice(MESSAGES.get(mood, MESSAGES["content"]))


def get_stage_name(stage):
    return STAGE_NAMES.get(stage, stage.title())


def render_bar(value, width=20):
    """Render a simple text progress bar, e.g. [##########----------] 50%"""
    value = max(0, min(100, value))
    filled = int(round((value / 100) * width))
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {value}%"
```

That's `art.py` done. Now let's build the actual command-line tool that ties everything together.

---

## Step 4: The CLI

Open `terminal_pet/cli.py`. We're using `argparse` from the standard library — no extra installs needed.

### Setting up colors and commands

A few ANSI color codes will make our stat bars pop:

```python
import argparse
import sys

from . import art
from .pet import Pet
from . import hooks


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"


def _color_for_value(value):
    if value >= 70:
        return Colors.GREEN
    elif value >= 35:
        return Colors.YELLOW
    return Colors.RED
```

### `pet init`

This creates the pet (if it doesn't exist yet) and installs the git hook:

```python
def cmd_init(args):
    pet = Pet()
    if pet.exists():
        print(f"You already have a pet named '{pet.state['name']}'!")
    else:
        name = args.name or "Buddy"
        pet = Pet()
        pet.create(name=name)
        print(f"🎉 You hatched a new pet... well, almost. Say hello to your egg, {name}!")
        print("Make your first commit to help it hatch.\n")

    success, message = hooks.install_hook(".")
    if success:
        print(f"✅ {message}")
        print("Every time you commit in this repo, your pet will be fed automatically.")
    else:
        print(f"⚠️  {message}")
        print("You can still use 'pet feed' and 'pet status' manually.")
```

Notice it's safe to run `pet init` again in a new repo even if you already have a pet — it'll just install the hook there without making a second pet. One pet, many repos.

### `pet status`

The big one — shows the ASCII art, stage, stat bars, and a message:

```python
def cmd_status(args):
    pet = Pet()
    if not pet.exists():
        print("You don't have a pet yet! Run 'pet init' to get started.")
        sys.exit(1)

    state = pet.state
    mood = pet.mood()
    stage = pet.stage()

    print(art.get_art(mood))
    print(f"{Colors.BOLD}{state['name']}{Colors.RESET} the {art.get_stage_name(stage)}")
    print()

    if stage != "egg":
        hunger = pet.hunger()
        happiness = pet.happiness()
        print(f"Hunger:    {_color_for_value(hunger)}{art.render_bar(hunger)}{Colors.RESET}")
        print(f"Happiness: {_color_for_value(happiness)}{art.render_bar(happiness)}{Colors.RESET}")
        print()
        print(f"Total commits:    {state['total_commits']}")
        print(f"Current streak:   {state['current_streak']} day(s)")
        print(f"Longest streak:   {state['longest_streak']} day(s)")
        print()

    print(f"{Colors.CYAN}{art.get_message(mood)}{Colors.RESET}")
```

We skip the stat bars while the pet is still an egg — it hasn't *done* anything yet!

### `pet feed`

This has two modes: a quiet one-liner (used by the git hook) and a fuller one for manual use:

```python
def cmd_feed(args):
    pet = Pet()
    if not pet.exists():
        if not args.quiet:
            print("You don't have a pet yet! Run 'pet init' to get started.")
        sys.exit(1)

    was_egg = pet.stage() == "egg"
    pet.feed()

    if args.quiet:
        if was_egg and pet.stage() != "egg":
            print(f"🎊 Your egg hatched! Say hello to {pet.state['name']} the "
                  f"{art.get_stage_name(pet.stage())}!")
        else:
            streak = pet.state["current_streak"]
            print(f"🍪 {pet.state['name']} has been fed! "
                  f"(streak: {streak} day{'s' if streak != 1 else ''})")
    else:
        print(f"You fed {pet.state['name']}! Hunger restored.")
        cmd_status(args)
```

The `--quiet` flag keeps the git hook's output to a single celebratory line instead of dumping the full status after every commit.

### `pet pet`

```python
def cmd_pet(args):
    pet = Pet()
    if not pet.exists():
        print("You don't have a pet yet! Run 'pet init' to get started.")
        sys.exit(1)

    if pet.stage() == "egg":
        print("It's still an egg... probably best not to poke it. Try committing some code!")
        return

    if pet.pet():
        print(f"{Colors.MAGENTA}You give {pet.state['name']} some pets. It seems happy!{Colors.RESET}")
    else:
        print(f"{pet.state['name']} has had enough attention for today. Try again tomorrow!")
```

### Wiring it all up with argparse

```python
def build_parser():
    parser = argparse.ArgumentParser(
        prog="pet",
        description="A virtual pet that lives in your terminal and reacts to your commits.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a new pet and install the git hook")
    init_parser.add_argument("--name", help="Name your pet", default=None)
    init_parser.set_defaults(func=cmd_init)

    status_parser = subparsers.add_parser("status", help="Show your pet's current state")
    status_parser.set_defaults(func=cmd_status)

    feed_parser = subparsers.add_parser("feed", help="Feed your pet (called automatically after commits)")
    feed_parser.add_argument("--quiet", action="store_true", help="Print a short message (used by the git hook)")
    feed_parser.set_defaults(func=cmd_feed)

    pet_parser = subparsers.add_parser("pet", help="Give your pet some attention")
    pet_parser.set_defaults(func=cmd_pet)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

The `set_defaults(func=...)` pattern is a neat argparse trick — each subcommand "remembers" which function should handle it, so `main()` just calls `args.func(args)` and lets argparse do the routing.

---

## Step 5: The git hook

Here's the piece that makes this feel automatic. Open `terminal_pet/hooks.py`.

The idea: when you run `pet init` inside a git repo, we write a small script into `.git/hooks/post-commit`. Git runs this script automatically after every commit.

```python
import os
import stat
import sys
from pathlib import Path

HOOK_NAME = "post-commit"

HOOK_TEMPLATE = """#!/bin/sh
# Installed by Terminal Pet -- feeds your pet after every commit.
{python} -m terminal_pet.cli feed --quiet
"""

APPEND_TEMPLATE = """
# --- Installed by Terminal Pet -- feeds your pet after every commit. ---
{python} -m terminal_pet.cli feed --quiet
"""
```

A couple of details worth calling out:

- We use `{python}` → `sys.executable`, which is the **full path** to the Python interpreter currently running our script. This avoids "command not found" issues if `pet` isn't on the `PATH` that git's hooks run with.
- We call `python -m terminal_pet.cli feed --quiet` rather than just `pet feed --quiet` for the same reason — it's more robust across environments.

### Finding the `.git` directory

```python
def find_git_dir(start_path="."):
    """Walk upward from start_path to find a .git directory."""
    path = Path(start_path).resolve()
    for parent in [path, *path.parents]:
        git_dir = parent / ".git"
        if git_dir.is_dir():
            return git_dir
    return None
```

This walks up the directory tree, so `pet init` works even if you run it from a subfolder of your repo.

### Installing the hook (without destroying existing hooks!)

This is the part I'm most proud of — a lot of tutorials would just overwrite `post-commit` and call it done, but that could wipe out something a teammate set up (like a linter or test runner). Instead, we check first:

```python
def install_hook(start_path="."):
    """Install (or upgrade) the post-commit hook in the current repo.

    Returns a tuple: (success: bool, message: str)
    """
    git_dir = find_git_dir(start_path)
    if git_dir is None:
        return False, "No .git directory found. Run this inside a git repository."

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hooks_dir / HOOK_NAME

    if hook_path.exists():
        existing = hook_path.read_text()
        if "Terminal Pet" in existing:
            return True, f"Hook already installed at {hook_path}"
        # Don't clobber an existing custom hook -- append instead.
        appended = existing.rstrip("\n") + "\n" + APPEND_TEMPLATE.format(python=sys.executable)
        hook_path.write_text(appended)
        _make_executable(hook_path)
        return True, f"Appended Terminal Pet hook to existing hook at {hook_path}"

    hook_path.write_text(HOOK_TEMPLATE.format(python=sys.executable))
    _make_executable(hook_path)
    return True, f"Installed post-commit hook at {hook_path}"


def _make_executable(path):
    current = os.stat(path).st_mode
    os.chmod(path, current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
```

Three cases handled:
1. **No hook exists** → write a fresh one.
2. **Our hook already exists** → do nothing (idempotent — running `pet init` twice is safe).
3. **A different hook already exists** → append our line to the end, so both run.

Don't forget `_make_executable` — git will silently skip hook scripts that aren't executable, which is a confusing bug to debug if you miss this step!

---

## Step 6: Make it installable

Last piece: `pyproject.toml`, so anyone (including you) can `pip install` this and get a global `pet` command.

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "terminal-pet"
version = "0.1.0"
description = "A virtual pet that lives in your terminal and reacts to your git commits"
readme = "README.md"
requires-python = ">=3.8"

[project.scripts]
pet = "terminal_pet.cli:main"

[tool.setuptools]
packages = ["terminal_pet"]
```

The important bit is `[project.scripts]` — this tells `pip` to create a `pet` executable that calls `main()` in `terminal_pet/cli.py`.

Install it in "editable" mode (so changes to your code take effect immediately, no reinstall needed):

```bash
pip install -e .
```

> 💡 On some systems (especially Linux with system Python), you may need:
> ```bash
> pip install -e . --break-system-packages
> ```
> or to use a virtual environment — `python -m venv venv && source venv/bin/activate` first.

---

## Step 7: Try it out!

Time for the fun part. Go to any git repo (or make a fresh test one):

```bash
mkdir my-test-repo && cd my-test-repo
git init
```

Now hatch your pet:

```bash
pet init --name "Pixel"
```

You should see something like:

```
🎉 You hatched a new pet... well, almost. Say hello to your egg, Pixel!
Make your first commit to help it hatch.

✅ Installed post-commit hook at .git/hooks/post-commit
Every time you commit in this repo, your pet will be fed automatically.
```

> 💡 **Add a screenshot here** of this output!

Check on your egg:

```bash
pet status
```

Now make a commit and watch it hatch:

```bash
echo "print('hello world')" > app.py
git add .
git commit -m "Initial commit"
```

You should see the hook fire automatically:

```
🎊 Your egg hatched! Say hello to Pixel the Hatchling!
```

> 💡 **Add a screenshot or short screen recording here** — this moment is the payoff!

Run `pet status` again to see your hatchling, full stat bars, and a 1-day streak. Try `pet pet` for a little affection, and try waiting a day (or faking it — see below) to watch hunger decay.

### Cheating time (for testing)

Want to see your pet get hungry without waiting 25 hours? You can manually edit `~/.terminal_pet/state.json` and roll `last_fed` back in time:

```python
import json
from pathlib import Path
from datetime import datetime, timedelta

state_file = Path.home() / ".terminal_pet" / "state.json"
with open(state_file) as f:
    state = json.load(f)

state["last_fed"] = (datetime.now() - timedelta(hours=20)).isoformat()

with open(state_file, "w") as f:
    json.dump(state, f, indent=2)
```

Run `pet status` afterward and watch your pet get progressively hungrier as you increase the hours. This is a great way to test your mood thresholds!

---

## Ideas for taking this further

You've got a fully working pet, but here are some directions to make it your own:

- **More evolution branches** — instead of one linear path, branch based on *how* you commit (lots of small commits vs. big ones, late-night commits, etc.) for different "species."
- **Multiple pets** — one per repo instead of one global pet.
- **A `pet history` command** — track commit times and show a little calendar heatmap, GitHub-contributions-graph style.
- **Sound effects** — use your terminal's bell (`\a`) for hatching or starving moments.
- **Slack/Discord integration** — post a message when your pet evolves or starts starving.
- **`pre-push` hook instead of (or in addition to) `post-commit`** — feed your pet only when code actually reaches a remote.

---

## Wrap-up

You just built a CLI tool, hooked it into git's automation system, and gave it a whole little personality system — all with the Python standard library. The core trick (compute decaying stats from timestamps instead of storing live values) is a pattern you'll see in a lot of places: cooldown timers, "last seen" indicators, rate limiters, and more.

Now go commit some code before Pixel gets hungry. 🐾

---

## Troubleshooting

### 'pet' is not recognized (Windows)

If you run `pet init` or `pet status` after installing and get a `'pet' is not recognized` error, your Python Scripts directory is likely not in your system's `PATH`.

**Quick fix (current terminal only):**
```powershell
$env:PATH += ";C:\Users\<username>\AppData\Local\Python\<python-version>\Scripts"
```
*(Make sure to replace `<username>` and `<python-version>` with your actual paths).*

**Permanent fix:**
Add your Python Scripts directory (e.g., `C:\Users\<username>\AppData\Local\Python\<python-version>\Scripts`) to your system's `PATH` environment variable via the Windows Environment Variables settings, then **restart your terminal**.
