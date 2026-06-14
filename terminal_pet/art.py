"""ASCII art and flavor messages for the Terminal Pet.

Each mood maps to a small piece of ASCII art and a list of possible
messages. A random message is chosen each time so the pet feels a
little more alive.
"""

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
