import random
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

class CardCollection:
    def __init__(self):
        self.cards: list[Card]
    
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

class GameDataConfig:
    def __init__(self, owner: discord.Member, config: dict | None = {
        "stackable": True,
        "effect_win": True,
        "min_players": 1,
        "max_players": 8
    }) -> None:
        # self.thread = thread
        self.owner = owner
        # self.stackable: bool = config.stackable
        # self.effect_win: bool = config.effect_win
        # self.min_players: int = config.min_players
        # self.max_players: int = config.max_players

class UNOGame:
    def __init__(self, data: GameDataConfig) -> None:
        self.players: list[Player] = [Player(data.owner)]
        self.deck: Deck = Deck()
        self.graveyard: Deck = Deck()
        self.currentIndex: int = 0
        self.is_clockwise: bool = True
        self.game_data_config: GameDataConfig = data
        # self.thread: discord.Thread = data.thread
        self.status: str = "Waiting"
    
    def add_player(self, user: discord.Member):
        # check if can add
        if self.status == "Started": return self.log("Game already started.")
        if user.id in [p.id for p in self.players]: return self.log("Player already in the list.")

        self.players.append(Player(user))
        return f"{user.display_name} joined the game succesfully."

    def del_player(self, player: Player):
        if player not in self.players: return self.log("Player is not in the list.")
        self.players.remove(player)

    def start_game(self):
        if self.status != "Waiting": return self.log("Game already started.")

        self.deck.generate_deck()
        random.shuffle(self.deck.cards)

        self.deal_cards()

        while(self.deck.last_card.isWild):
            random.shuffle(self.deck.cards)
        
        self.graveyard.add_card(self.deck.pop_card())

        self.status = "Started"


    def deal_cards(self):
        for player in self.players:
            for x in range(7):
                player.hand.add_card(self.deck.pop_card())

    def log(self, message: str) -> str:
        return message
    
class GameView(discord.ui.View):
    
    game: UNOGame

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
            await interaction.response.send_message(content="Starting game...", ephemeral=True)
            self.stop()
        
    @discord.ui.button(label="Join", style=discord.ButtonStyle.primary, custom_id="join")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(content=f"{self.game.add_player(user=interaction.user)}", ephemeral=True)


class Main:

    def __init__(self, ctx) -> None:
        self.ctx = ctx

    async def start_main(self):
        try:
            # views
            start_view = StartMenu(timeout=600)

            # game init
            game = UNOGame(GameDataConfig(owner=self.ctx.user, config=None))
            game_message : discord.WebhookMessage = await self.ctx.followup.send(content="Uno game started", view=start_view, wait=True)
            start_view.game = game

            await start_view.wait()
        except:
            print("error")
        finally:
           await game_message.edit(view=None)
        


