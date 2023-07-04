from dataclasses import dataclass
from enum import Enum

import discord


@dataclass
class GameConfig:
    client: discord.Client
    thread: discord.Thread | None = None
    owner: discord.Member | None = None
    max_players: int = 8
    min_players: int = 2


class GameState(Enum):
    WAITING = 1
    PLAYING = 2
    FINISHED = 3
    CANCELLED = 4
    NONE = 5
