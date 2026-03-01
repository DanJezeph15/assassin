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


## Screenshots:
<img width="335" height="749" alt="Screenshot 2026-03-01 at 19 20 50" src="https://github.com/user-attachments/assets/628b2d12-b0a9-4e71-82de-c9a32747a333" />

<img width="391" height="412" alt="Screenshot 2026-03-01 at 19 22 05" src="https://github.com/user-attachments/assets/a25a718f-6e73-46f0-80ab-0adfcc467116" />

<img width="314" height="671" alt="Screenshot 2026-03-01 at 19 22 36" src="https://github.com/user-attachments/assets/99cbd7a1-2138-4084-ab6b-72d99e2e395d" />

<img width="324" height="531" alt="Screenshot 2026-03-01 at 19 23 09" src="https://github.com/user-attachments/assets/014a3210-62c4-4dc1-8ae8-8435b9fa764f" />
