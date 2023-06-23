
from dataclasses import dataclass
from enum import Enum
from ..uno.card_collection import Hand
import discord

@dataclass
class GameConfig:
    owner: discord.Member

class GameState(Enum):
    WAITING = 1
    PLAYING = 2
    FINISHED = 3
    CANCELLED = 4

class Player:
    def __init__(self, user: discord.Member) -> None:
        self.name = user.display_name
        self.id = user.id
        self.hand = Hand()
        self.warns = 0

class BaseGame:
    def __init__(self, data: GameConfig) -> None:
        self.players: list[Player] = [Player(data.owner)]
        self.current_player_index: int = 0
        self.is_clockwise: bool = True
        self.game_data_config: GameConfig = data
        self.status: GameState = GameState.WAITING

    def add_player(self, user: discord.Member):
        # check if can add
        if self.status == GameState.PLAYING: return print("Game already started...")
        if user.id in [p.id for p in self.players]: return print("Player already in the list.")

        self.players.append(Player(user))
        return f"{user.display_name} joined the game succesfully."

    def del_player(self, player: Player):
        if player not in self.players: return print("Game already started...")
        self.players.remove(player)
    
    def start_game(self): ...

    def get_player_by_id(self, id: int) -> Player | None:
        player = next((p for p in self.players if p.id == id), None)
        return player
    
    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_index]