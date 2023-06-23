import random
import discord
from enum import Enum
from typing import TypeVar
from dataclasses import dataclass
from discord.components import SelectOption

CardType = TypeVar('CardType', bound='Card')

@dataclass
class GameConfig:
    owner: discord.Member
    stackable: bool = True
    effect_win: bool = True
    turn_time: float = 180
    min_players: int = 1
    max_players: int = 8


class GameState(Enum):
    WAITING = 1
    PLAYING = 2
    FINISHED = 3
    CANCELLED = 4

class Card:
    def __init__(self, color: str, value: str) -> None:
        self.color: str = color
        self.value: str = value
        self.id = random.randint(0, 2000)

    def validate(self, card: CardType):
        return self.color == card.color or self.value == card.value or self.is_wild

    @property
    def is_wild(self):
        return self.color == "WILD"

    @property
    def has_effect(self):
        effects: dict = {
            "+2": True,
            "SKIP": True,
            "REVERSE": True
        }
        return effects.get(self.value, False)
    
    @property
    def color_code(self) -> int:
        colors: dict = {
            "R": 0xff5555,
			"Y": 0xffaa00,
			"G": 0x55aa55,
			"B": 0x5555ff
        }
        return colors.get(self.color, 0x080808)
    
    @property
    def image_url(self) -> str:
        return f"https://raw.githubusercontent.com/Ratismal/UNO/master/cards/{self.color}{self.value}.png"

    @property
    def name(self) -> str:
        color_name: dict = {
            "R": "Red",
            "B": "Blue",
            "Y": "Yellow",
            "G": "Green"
        }
        return f"{color_name.get(self.color,'Wild')} {self.value}"

    def __str__(self) -> str:
        return f"{self.color}{self.value}"

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

class CardFilterFunctions:
    def __init__(self) -> None:
        filters = {
            1: self.plus_two_filter,
            2: self.no_effect_win_filter
        }

    def filter(self, filter_value:int, cards: list[Card], last_card: Card) -> list[Card] | None:
        return self.filters.get(filter_value, None)(cards, last_card)
    
    def plus_two_filter(self, cards: list[Card], last_card) -> list[Card] | None:
        new_hand = []
        for card in cards:
            if card.value == "+2": new_hand.append(card)
        return new_hand
                
    def no_effect_win_filter(self, cards: list[Card], last_card) -> list[Card] | None:
        new_hand = []
        for card in cards:
            if not card.has_effect: new_hand.append(card) and card.validate(last_card)
        return new_hand

class CardFilter(Enum):
    PLUS_TWO_STACK = 1
    NO_EFFECT_WIN = 2

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

    def get_card_by_id(self, id: str) -> Card | None:
        card = next((c for c in self.cards if c.id == int(id)), None)
        return card
    
    def generate_valid_hand(self, last_card: Card, filter: CardFilter | None = None) -> list[Card]:
        cards: list[Card] = []

        if filter is None:
            for card in self.cards:
                if card.validate(last_card): cards.append(card)
        
        if filter is CardFilter:
            cards = CardFilterFunctions.filter(filter_value=filter.value,cards=self.cards, last_card=last_card)
        
        return cards


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
    
    @property
    def player_list(self) -> str:
        list = ""
        if self.status == GameState.WAITING:
            for player in self.players:
                list += f"- {player.name}\n"
        else:
            for player in self.players:
                if player is self.current_player:
                    list += f"▶ {player.name} ({len(player.hand.cards)} {'cards' if len(player.hand.cards) != 1 else 'card'})\n"
                else:
                    list += f"- {player.name} ({len(player.hand.cards)} {'cards' if len(player.hand.cards) != 1 else 'card'})\n"
        return list

class UNOGame(BaseGame):
    def __init__(self, data: GameConfig) -> None:
        super().__init__(data)
        self.deck: Deck = Deck()
        self.graveyard: Deck = Deck()
        self.last_action: str = "Game started with: "
        self.winner: Player
        # self.thread: discord.Thread = data.thread

    def start_game(self):
        if self.status != GameState.WAITING: return print("Game already started...")

        self.deck.generate_deck()
        random.shuffle(self.deck.cards)

        self.deal_cards()

        while(self.deck.last_card.is_wild):
            random.shuffle(self.deck.cards)
        
        self.graveyard.add_card(self.deck.pop_card())

        self.status = GameState.PLAYING

    """
    Changes the current_index value, can't be higher than the length of the players list.
    If is_clockwise current_index value will cycle reversed.
    """
    def skip_turn(self):
        self.check_win()

        if self.is_clockwise:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
        else:
            self.current_player_index = (self.current_player_index - 1 + len(self.players)) % len(self.players)
        
    def check_win(self):
        if len(self.current_player.hand.cards) == 0:
            self.status = GameState.FINISHED
            self.winner = self.current_player
    
    def change_orientation(self):
        self.is_clockwise = not self.is_clockwise

    """
    Check if the player has his turn.
    Check if the card sended exists in the player hand.
    Check if the card is a valid play. # Wild should be colorized before play_card().
    Send Card to the graveyard
    Skip Turn
    If Card has Effect resolve Card Effect (For the next player)
    """
    async def play_card(self, player: Player, card) -> Card | None:
        if player is not self.current_player: return None
        card: Card = player.hand.get_card_by_id(card)
        if card == None: return print("ERROR: Card doesn't exist")

        # play process
        player.hand.del_card(card)
        self.last_action = f"{player.name} sent a card: "
        self.graveyard.add_card(card)
        self.skip_turn()

        return card
    
    """
    Levanta una carta y retorna la carta levantada.
    """
    async def draw_card(self, player: Player) -> Card:
        card = self.deck.pop_card()
        player.hand.add_card(card)
        return card

    """
    Deal 7 cards for each player in the list.
    """
    def deal_cards(self):
        for player in self.players:
            for x in range(7):
                player.hand.add_card(self.deck.pop_card())


class GameView(discord.ui.View):    
    def __init__(self, *, timeout: float | None = 180, game):
        super().__init__(timeout=timeout)
        self.game : BaseGame | UNOGame = game

    async def disable_all_items(self, interaction: discord.Interaction):
        for item in self.children:
            item.disabled = True
        await interaction.original_response.edit(view=self)

class StartMenu(GameView):

    msg: discord.WebhookMessage
    embed: discord.Embed

    @discord.ui.button(label="Start", style=discord.ButtonStyle.primary, custom_id="start")
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if interaction.user.id != self.game.game_data_config.owner.id:
            await interaction.response.send_message(content="You cannot start this game.", ephemeral=True)
            return
        else:
            await self.msg.edit(view=None)
            self.game.start_game()
            self.stop()
        
    @discord.ui.button(label="Join", style=discord.ButtonStyle.primary, custom_id="join")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(content=f"{self.game.add_player(user=interaction.user)}", ephemeral=True)
        self.embed.description = f"{self.game.player_list}"
        await self.msg.edit(embed=self.embed, view=self)

class CardSelectItem(discord.SelectOption):
    ...

class CardSelectMenu(discord.ui.Select):
    def __init__(self, *, custom_id: str = ..., placeholder: str | None = None, min_values: int = 1, max_values: int = 1, options: List[SelectOption] = ..., disabled: bool = False, row: int | None = None, cards: list[Card], game: UNOGame) -> None:
        super().__init__(custom_id=custom_id, placeholder=placeholder, min_values=min_values, max_values=max_values, options=options, disabled=disabled, row=row)
        self.cards: list[Card] = cards
        self.game: UNOGame = game
        for card in cards:
            item = CardSelectItem(label=f"{card.name}", value=f"{card.id}")
            self.append_option(option=item)

    # send the card item value to the game, the game will search for the card in the hand and send it to graveyard.
    async def callback(self, interaction: discord.Interaction):
        card_id = interaction.data.get('values')[0]
        player = self.game.get_player_by_id(interaction.user.id)
        card: Card | None = await self.game.play_card(player, card_id)
        if card == None:
            await interaction.response.send_message(content="Is not your turn...", ephemeral=True)
        else:
            await interaction.response.send_message(content=f"You sent {card.name}", ephemeral=True)
        self.view.stop()


class CardSelect(GameView):
    def __init__(self, *, timeout: float | None = 180, game, game_view: GameView, card_list: list[Card] | None):
        super().__init__(timeout=timeout, game=game)
        self.game_view = game_view
        self.card_list = card_list
    
    async def generate_hand(self):
        if self.card_list == None: return print("This player doesn't have cards to throw")
        valid_hand = CardSelectMenu(custom_id="send_card", cards=self.card_list, options=[], game=self.game)
        self.add_item(valid_hand)

    """Chequea si es turno del usuario que interactuó"""
    async def interaction_check(self, interaction: discord.Interaction):
        return self.game.players[self.game.current_player_index].id == interaction.user.id

        
class DrawSelectView(GameView):
    def __init__(self, *, timeout: float | None = 180, game, game_view: GameView):
        super().__init__(timeout=timeout, game=game)
        self.game_view: GameView = game_view
    
    """
    @TODO: Send card to game
    """
    @discord.ui.button(label="Tirar")
    async def throw(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(content="You sent a card", ephemeral=True)
        await self.game_view.draw_message.delete()
        self.game.last_action = f"{self.game.players[self.game.current_player_index].name} picked up a card and threw it: "
        self.game_view.stop()
        self.stop()
    @discord.ui.button(label="Saltar")
    async def keep(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(content="You kept the card", ephemeral=True)
        await self.game_view.draw_message.delete()
        self.game.last_action = f"{self.game.players[self.game.current_player_index].name} picked up a card, the last card is: "
        self.game_view.stop()
        self.stop()

class GameMenu(GameView):
    def __init__(self, *, timeout: float | None = 180, game):
        super().__init__(timeout=timeout, game=game)
        self.card_select_view: GameView | None = None
        self.draw_select_view: DrawSelectView | None = None
    
    foo: bool = False

    """
    check player turn, if is not just give emoji cards
    """
    @discord.ui.button(label="Hand", style=discord.ButtonStyle.green, custom_id="hand")
    async def hand(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self.game.get_player_by_id(interaction.user.id) # obtain player from the list
        if player == self.game.players[self.game.current_player_index]:
            hand = player.hand.generate_valid_hand(last_card=self.game.graveyard.last_card)

            if len(hand) == 0:
                # No tienes cartas para tirar
                await interaction.response.send_message("You don't have any valid card.") # REPLACE WITH EMOJIS
            else:
                self.card_select_view = CardSelect(game=self.game, timeout=120, game_view=self, card_list=hand)
                await self.card_select_view.generate_hand()
                await interaction.response.defer(ephemeral=True)
                self.hand_message = await interaction.followup.send(content="REPLACE WITH EMOJIS", ephemeral=True, wait=True, view=self.card_select_view)
                await self.card_select_view.wait()
                self.stop()
        else:
            await interaction.response.send_message(content="No es tu turno pedazo de pelotudo", ephemeral=True)

    """
    check player turn, if is not just return ephemeral message "it's' not your turn"
    """
    @discord.ui.button(label="Draw", style=discord.ButtonStyle.grey, custom_id="draw")
    async def draw(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.card_select_view != None: self.card_select_view.stop()
        if self.foo == True: return
        player = self.game.get_player_by_id(interaction.user.id)
        if player == self.game.players[self.game.current_player_index]:
            card = await self.game.draw_card(player)
            if card.validate(self.game.graveyard.last_card):
                print(f"La puedes tirar: {card}")
                self.foo = True
                # TODO
                await interaction.response.defer(ephemeral=True)
                self.draw_select_view = DrawSelectView(game=self.game, timeout=120, game_view=self)
                self.draw_message = await interaction.followup.send(content=f"Levantaste {card}, la queri tira?", ephemeral=True, wait=True, view=self.draw_select_view)
                await self.draw_select_view.wait()
            else:
                print(f"No la puedes tirar: {card}")
                self.game.last_action = f"{player.name} picked up a card, the last card is: "
                await interaction.response.send_message(content="You draw a card", ephemeral=True)
            self.stop()
        else:
            await interaction.response.send_message(content="No es tu turno, no entiendes? pedazo de inútil", ephemeral=True)
    
    """
    Chequea si el usuario que interactuó realmente está jugando.
    """
    async def interaction_check(self, interaction: discord.Interaction):
        player = self.game.get_player_by_id(interaction.user.id)
        if player not in self.game.players:
            await interaction.response.send_message("No estás jugando")
            return False
        else: return True

"""
Clase involucrada en enviar mensajes, recibir comandos, hacer el manejo entero del juego usando la GameClass y
además va accionar en base a los resultados al final del juego.
"""
class Main:
    def __init__(self, ctx) -> None:
        self.ctx : discord.Interaction = ctx # First command interaction
        self.game : UNOGame = UNOGame(GameConfig(owner=ctx.user))
  
    async def start(self):
        self.main_view : GameView = StartMenu(game=self.game)
        await self.game_state_message() # ingresa al bucle

    async def game_state_message(self):
        if self.game.status == GameState.WAITING:
            # Juego no iniciado
            await self.main_menu_message(ctx=self.ctx, view=self.main_view)
            await self.main_view.wait()
        elif self.game.status == GameState.PLAYING:
            # Juego iniciado
            self.game_view = GameMenu(timeout=None,game=self.game)
            await self.game_menu_message(ctx=self.ctx, view=self.game_view)
            await self.game_view.wait()
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
        await ctx.response.defer()
        embed = discord.Embed(title="UNO Beta")
        embed.description = f"```markdown\n{self.game.player_list}```"
        start_msg = await ctx.followup.send(embed=embed, view=view)
        view.msg = start_msg
        view.embed = embed

    async def game_menu_message(self, ctx: discord.Interaction, view: GameView):
        embed = discord.Embed(title="UNO Beta", color=self.game.graveyard.last_card.color_code, description=(
            f"{self.game.last_action + self.game.graveyard.last_card.name}\n"
            f"```markdown\n{self.game.player_list}```"
        ))
        embed.set_thumbnail(url=self.game.graveyard.last_card.image_url)
        await ctx.channel.send(embed=embed, view=view)