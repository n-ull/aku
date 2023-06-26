import discord
from enum import Enum
from dataclasses import dataclass

@dataclass
class GameConfig:
    client: discord.Client
    thread: discord.TextChannel
    owner = None
    max_players: int = 8
    min_players: int = 1

class GameState(Enum):
    WAITING = 1
    PLAYING = 2
    FINISHED = 3
    CANCELLED = 4
    NONE = 5