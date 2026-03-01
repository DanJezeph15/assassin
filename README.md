# Assassin

A real-life elimination game for groups staying at an Airbnb. Think Cluedo but you're actually doing it — each player is secretly assigned a target to "kill" using a specific weapon in a specific room of the house.

## How It Works

1. **One person creates a game** and shares the join code with everyone.
2. **Players join** the lobby and enter their name.
3. **Everyone adds rooms and weapons** — real rooms in your Airbnb (Kitchen, Master Bedroom, etc.) and real objects as weapons (Mug, Spatula, TV Remote, etc.).
4. **The host starts the game** and everyone gets a secret assignment: **"Kill [Target] in the [Room] with the [Weapon]"**.

## Playing the Game

- Your assignment is private — only you can see it.
- To make a kill, get your target alone in the assigned room with the assigned weapon. Creativity and stealth encouraged.
- When you're killed, you confirm it by pressing **"I've been killed"** in the app.
- The killer then inherits the victim's assignment and continues the hunt.
- Last person standing wins.

## Leaderboard

Kills are tracked per player throughout the game, so even if you're eliminated you can see who's dominating.

## Running It

You'll need Python 3.12+ and Node.js 18+.

```bash
# Install everything
make setup

# Start the app
make dev
```

Then open http://localhost:5173 and share the join code with your friends.

## Technical Details

See [CLAUDE.md](CLAUDE.md) for the tech stack, project structure, and detailed game logic.
