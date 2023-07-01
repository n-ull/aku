from dataclasses import dataclass
from game_base.game_state import GameConfig

@dataclass
class UnoGameConfig(GameConfig):
    min_players: int = 1
    stackable: bool = True
    effect_win: bool = True
    randomize_players: bool = False
    turn_time: float = 180