import discord
from enum import Enum
from dataclasses import dataclass

@dataclass
class GameConfig:
    owner: discord.Member
    ctx: discord.Client
    max_players: int = 8
    min_players: int = 1

class GameState(Enum):
    WAITING = 1
    PLAYING = 2
    FINISHED = 3
    CANCELLED = 4
    NONE = 5