# Terminal Pet 🐾

A virtual pet that lives in your terminal and reacts to your git commits.
Commit code to feed it, build up streaks to keep it happy, and watch it
evolve from an egg into a legendary creature.

## Install

```bash
git clone <this-repo>
cd terminal-pet
pip install -e .
``` 

This installs a `pet` command on your system.

## Usage

Inside any git repository:

```bash
pet init --name "Pixel"
```

This creates your pet and installs a `post-commit` git hook in that repo.
From now on, every `git commit` will automatically feed your pet.

Check on your pet any time:

```bash
pet status
```

Give it some attention (limited to 3 times per day):

```bash
pet pet
```

## How it works

- Your pet's data lives in `~/.terminal_pet/state.json`.
- Hunger drains over time based on how long it's been since your last
  commit (4 points per hour).
- Happiness is based on hunger plus a bonus for active commit streaks.
- Your pet evolves through stages (Egg → Hatchling → Sprout → Adult →
  Legendary) as your total commit count grows.
- A `post-commit` hook calls `pet feed --quiet` automatically -- no
  background processes or daemons required.

## Commands

| Command       | Description                                      |
|---------------|---------------------------------------------------|
| `pet init`    | Create a pet and install the git hook in this repo |
| `pet status`  | Show your pet's mood, stats, and stage            |
| `pet feed`    | Manually feed your pet                            |
| `pet pet`     | Give your pet some attention (3x/day max)         |
