"""Command-line interface for Terminal Pet.

Commands:
    pet init [--name NAME]   Create a new pet and install the git hook
    pet status               Show your pet's current state
    pet feed                 Manually feed your pet (also called by the hook)
    pet pet                  Give your pet some attention (limited per day)
"""

import argparse
import sys

from . import art
from .pet import Pet
from . import hooks


# ANSI color codes -- kept minimal and dependency-free.
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


def cmd_feed(args):
    pet = Pet()
    if not pet.exists():
        if not args.quiet:
            print("You don't have a pet yet! Run 'pet init' to get started.")
        sys.exit(1)

    was_egg = pet.stage() == "egg"
    pet.feed()

    if args.quiet:
        # This is the message shown right after a git commit -- keep it short.
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
