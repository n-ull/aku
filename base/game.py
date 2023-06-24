from random import shuffle
from discord import Member
from game_base.game_state import GameState, GameConfig
from game_base.player import Player

class BaseGame:
    def __init__(self, data: GameConfig) -> None:
        self.players: list[Player] = [Player(data.owner)]
        self.current_player_index: int = 0
        self.is_clockwise: bool = True
        self.game_data_config: GameConfig = data
        self.status: GameState = GameState.WAITING

    def add_player(self, user: Member):
        # check if can add
        if self.status == GameState.PLAYING: return
        if user.id in [p.id for p in self.players]: return f"You are already in the game..."
        if len(self.players) == self.game_data_config.max_players: return f"Maximum players: {self.game_data_config.max_players}"

        self.players.append(Player(user))
        return f"{user.display_name} joined the game succesfully."

    def del_player(self, player: Player):
        if player not in self.players: return print("Game already started...")
        self.players.remove(player)
    
    def start_game(self): ...

    def skip_turn(self): ...

    def punish_user(self): ...

    def randomize_players(self):
        shuffle(self.players)

    def get_player_by_id(self, id: int) -> Player | None:
        player = next((p for p in self.players if p.id == id), None)
        return player
    
    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_index]
    
    @property
    def next_player(self) -> Player:
        return self.players[(self.current_player_index + 1) % len(self.players)]