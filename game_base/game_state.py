from dataclasses import dataclass
from enum import Enum

import discord


@dataclass
class GameConfig:
    owner: discord.Member
    ctx: discord.Client
    max_players: int = 8
    min_players: int = 2


class GameState(Enum):
    WAITING = 1
    PLAYING = 2
    FINISHED = 3
    CANCELLED = 4
    NONE = 5
