import random
from threading import Timer
from typing import Optional
import discord
from discord.interactions import Interaction

class Card:
    def __init__(self, color: str, value: str) -> None:
        self.color: str = color
        self.value: str = value

    @property
    def is_wild(self):
        return self.color == "WILD"

    @property
    def has_effect(self):
        effects: dict = {
            "SKIP": True,
            "+2": True,
            "REVERSE": True
        }
        return effects.get(self.value, False)
    
    def __str__(self) -> str:
        return f"{self.color} {self.value}"

class CardCollection:
    def __init__(self):
        self.cards: list[Card] = []
    
    def add_card(self, card: Card):
        self.cards.append(card)
    
    def del_card(self, card:Card):
        self.cards.remove(card)
    
    @property
    def last_card(self):
        return self.cards[-1]

class Deck(CardCollection):
    def __init__(self):
        super().__init__()

    def generate_deck(self):
        colors = ["R", "G", "B", "Y"]
        values = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "SKIP", "REVERSE", "+2"]
        for color in colors:
            for value in values:
                self.cards.append(Card(color, value))
                self.cards.append(Card(color, value))
        for x in range(4):
            self.cards.append(Card('WILD', 'WILD'))
            self.cards.append(Card('WILD', 'WILD+4'))
    
    def pop_card(self) -> Card:
        return self.cards.pop()
        

class Hand(CardCollection):
    def __init__(self):
        super().__init__()

class Player:
    def __init__(self, user: discord.Member) -> None:
        self.name = user.display_name
        self.id = user.id
        self.hand = Hand()
        self.warns = 0

class GameDataConfigBase:
    def __init__(self, owner: discord.Member) -> None:
        self.owner = owner
        
class BaseGame:
    def __init__(self, data: GameDataConfigBase) -> None:
        self.players: list[Player] = [Player(data.owner)]
        self.currentIndex: int = 0
        self.is_clockwise: bool = True
        self.game_data_config: GameDataConfigBase = data
        self.status: str = "Waiting"
        self.timer: Timer | None = None

    def add_player(self, user: discord.Member):
        # check if can add
        if self.status == "Started": return self.log("Game already started.")
        if user.id in [p.id for p in self.players]: return self.log("Player already in the list.")

        self.players.append(Player(user))
        return f"{user.display_name} joined the game succesfully."

    def del_player(self, player: Player):
        if player not in self.players: return self.log("Player is not in the list.")
        self.players.remove(player)
    
    def start_game(self): ...

    def get_player_by_id(self, id: int) -> Player | None:
        player = next((p for p in self.players if p.id == id), None)
        return player
    
    @property
    def player_list(self) -> str:
        list = ""
        for player in self.players:
            list += player.name
        return list

class GameDataConfig(GameDataConfigBase):
    def __init__(self, owner: discord.Member, config: dict | None = {
        "stackable": True,
        "effect_win": True,
        "min_players": 1,
        "max_players": 8,
        "turn_time": 180 # in seconds
    }) -> None:
        super().__init__(owner)
        self.stackable: bool = config["stackable"]
        self.effect_win: bool = config["effect_win"]
        self.min_players: int = config["min_players"]
        self.max_players: int = config["max_players"]
        self.turn_time: float = config["turn_time"]
        # self.thread = thread

class UNOGame(BaseGame):
    def __init__(self, data: GameDataConfig) -> None:
        super().__init__(data)
        self.deck: Deck = Deck()
        self.graveyard: Deck = Deck()
        # self.thread: discord.Thread = data.thread

    def start_game(self):
        if self.status != "Waiting": return self.log("Game already started.")

        self.deck.generate_deck()
        random.shuffle(self.deck.cards)

        self.deal_cards()

        while(self.deck.last_card.is_wild):
            random.shuffle(self.deck.cards)
        
        self.graveyard.add_card(self.deck.pop_card())

        self.status = "Started"

    """
    Changes the current_index value, can't be higher than the length of the players list.
    If is_clockwise current_index value will cycle reversed.
    """
    def skip_turn(self):
        ...
    
    """
    Check if the player has his turn.
    Check if the card sended exists in the player hand.
    Check if the card is a valid play. # Wild should be colorized before play_card().
    Send Card to the graveyard
    Skip Turn
    If Card has Effect resolve Card Effect (For the next player)
    """
    def play_card(self, player, card):
        ...

    """
    Deal 7 cards for each player in the list.
    """
    def deal_cards(self):
        for player in self.players:
            for x in range(7):
                player.hand.add_card(self.deck.pop_card())

    def log(self, message: str) -> str:
        return message
    
class GameView(discord.ui.View):    
    def __init__(self, *, timeout: float | None = 180, game):
        super().__init__(timeout=timeout)
        self.game : BaseGame = game

    async def disable_all_items(self, interaction: discord.Interaction):
        for item in self.children:
            item.disabled = True
        await interaction.original_response.edit(view=self)

class StartMenu(GameView):

    @discord.ui.button(label="Start", style=discord.ButtonStyle.primary, custom_id="start")
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.game.game_data_config.owner.id:
            await interaction.response.send_message(content="You cannot start this game.", ephemeral=True)
            return
        else:
            self.game.start_game()
            self.stop()
        
    @discord.ui.button(label="Join", style=discord.ButtonStyle.primary, custom_id="join")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(content=f"{self.game.add_player(user=interaction.user)}", ephemeral=True)

class CardSelect(GameView):
    def __init__(self, *, timeout: float | None = 180, game, game_view: GameView):
        super().__init__(timeout=timeout, game=game)
        self.game_view = game_view
    
    @discord.ui.button(label="This card", style=discord.ButtonStyle.primary, custom_id="cardid")
    async def play(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(content="You sent a card", ephemeral=True)
        await self.game_view.hand_message.delete()
        self.game_view.stop()
        self.stop()

class GameMenu(GameView):
    def __init__(self, *, timeout: float | None = 180, game):
        super().__init__(timeout=timeout, game=game)
        self.card_select_view: GameView | None = None
    
    @discord.ui.button(label="Hand", style=discord.ButtonStyle.green, custom_id="hand")
    async def hand(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        self.hand_message = await interaction.followup.send(content="Your hand", ephemeral=True, wait=True, view=self.card_select_view)

    @discord.ui.button(label="Draw", style=discord.ButtonStyle.grey, custom_id="draw")
    async def draw(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(content="You draw a card", ephemeral=True)

"""
Clase involucrada en enviar mensajes, recibir comandos, hacer el manejo entero del juego usando la GameClass y
además va accionar en base a los resultados al final del juego.
"""
class Main:
    def __init__(self, ctx) -> None:
        self.ctx : discord.Interaction = ctx # First command interaction
        self.game : UNOGame = UNOGame(GameDataConfig(owner=ctx.user))
  
    async def start(self):
        self.main_view : GameView = StartMenu(game=self.game)
        await self.game_state_message() # ingresa al bucle

    async def game_state_message(self):
        if self.game.status == "Waiting":
            # Juego no iniciado
            await self.main_menu_message(ctx=self.ctx, view=self.main_view)
            await self.main_view.wait()
        elif self.game.status == "Started":
            # Juego iniciado
            self.game_view = GameMenu(timeout=None,game=self.game)
            self.card_select_view = CardSelect(timeout=None,game=self.game, game_view=self.game_view)

            # give card select view to hand
            self.game_view.card_select_view = self.card_select_view

            await self.game_menu_message(ctx=self.ctx, view=self.game_view)
            await self.game_view.wait()
            await self.card_select_view.wait()
        else:
            # Juego terminado o cancelado
            self.end_cycle()
            return
            ...
        await self.game_state_message()

    """
    Enviar resultado final
    """
    async def end_cycle(self):
        ...

    async def main_menu_message(self, ctx: discord.Interaction, view: GameView):
        embed = discord.Embed(title="UNO Beta", description=f"{self.game.player_list}")
        await ctx.response.send_message(embed=embed, view=view)

    async def game_menu_message(self, ctx: discord.Interaction, view: GameView):
        embed = discord.Embed(title="UNO Beta", description=f"{self.game.graveyard.last_card}\n{self.game.player_list}")
        await ctx.channel.send(embed=embed, view=view)




