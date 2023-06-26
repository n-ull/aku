from random import shuffle
from discord import Member, TextChannel
from .game_state import GameState, GameConfig
from .player import Player

class GameBase:
    def __init__(self, data: GameConfig) -> None:
        self.players: list[Player] = []
        self.current_player_index: int = 0
        self.is_clockwise: bool = True
        self.data: GameConfig = data
        self.thread: TextChannel = data.thread #TODO: Change to Thread
        self.status: GameState = GameState.WAITING

    def add_player(self, user: Member):
        # check if can add
        if self.status == GameState.PLAYING: return
        if user.id in [p.id for p in self.players]: return f"You are already in the game..."
        if len(self.players) == self.data.max_players: return f"Maximum players: {self.data.max_players}"

        self.players.append(Player(user))
        return f"{user.display_name} joined the game succesfully."

    def del_player(self, player: Player):
        if player not in self.players: return print("Game already started...")
        self.players.remove(player)
    
    def start_game(self): ...

    def skip_turn(self): ...

    def warn_player(self, func = None):
        if self.current_player.warns == 2:
            self.del_player(self.current_player)
            if len(self.players) == 1:
                self.status = GameState.CANCELLED
        else:
            self.current_player.warns += 1
            if func is not None:
                func()
            self.skip_turn()
    
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