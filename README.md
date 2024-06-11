# Cachex AI Bot

This repository contains an AI bot designed to play the game of Cachex, a two-player connection game. The bot uses various game-playing techniques to strategize and compete effectively against an opponent.

## Overview

Cachex is a strategic two-player game where the objective is to form an unbroken chain of stones between opposing sides of a hexagonally tiled board. This project involves building an AI agent that can play Cachex, utilizing advanced algorithms and strategies.

## Game Rules

### Basic Rules
- The game is played on an n x n rhombic, hexagonally tiled board.
- Two players, Red and Blue, take turns placing stones on empty hexes (Red always plays first).
- The goal is to connect opposite sides of the board with an unbroken chain of stones of their color.

### Special Mechanisms
- **Swap Mechanism**: Blue can steal Red's first move by reflecting it across the board's central axis.
- **Capture Mechanism**: If a symmetric 2x2 diamond of hexes is formed with two stones from each player, the player completing the diamond removes the opponent's stones from the diamond.
- **Game End Conditions**: The game ends when a player forms an unbroken connection, a specific game configuration repeats seven times, or 343 turns pass without a winner.

## Project Structure

- `playing_agent/`: Directory containing the the main implementation module for the AI bot.
- `random_agent/`: Directory containing the module for a bot that makes moves randomly (used for testing purposes).
- `referee/`: Directory containing the referee program to facilitate games between two AI agents.

## Usage

To run a game of Cachex between two AI agents:

1. Ensure you have Python 3.6 installed.
2. Place the `referee` module and your `playing_agent` module in the same directory.
3. Run the referee program with the appropriate command:

    ```bash
    python -m referee <n> <red_module> <blue_module>
    ```

Where:
- `<n>` is the size of the game board.
- `<red_module>` is the name of the module containing the Player class for Red.
- `<blue_module>` is the name of the module containing the Player class for Blue.

For example, if both players are defined in the `playing_agent` module:

    python -m referee 8 playing_agent playing_agent

## Implementation Details

### Player Class

The `Player` class in the `playing_agent` module contains three essential methods:

- `__init__(self, player, n)`: Initializes the player with the specified color and board size.
- `action(self)`: Determines and returns the next move based on the current game state.
- `turn(self, player, action)`: Updates the game state after a player's move.

### Strategies and Algorithms

The AI bot employs various strategies and algorithms to make informed decisions. These include:
- Minimax algorithm with alpha-beta pruning for efficient decision-making.
- Heuristics to evaluate board states and prioritize moves.
- Techniques to handle the capture mechanism and the swap rule effectively.
- Designed to compete against bots of increasing difficulty.

## Example Games

**Random Agent VS Playing Agent**:

![Random Agent VS Playing Agent](https://github.com/AbrarS242/AI-cachex-player/blob/main/example_games/random_vs_player.PNG)

**Playing Agent VS Playing Agent**:

![Random Agent VS Playing Agent](https://github.com/AbrarS242/AI-cachex-player/blob/main/example_games/player_vs_player.PNG)
