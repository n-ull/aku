import random
import discord
import settings
from dataclasses import dataclass

# game imports
from ..base.base_game import BaseGame, GameConfig, GameState, Player
from .card import Card
from .card_collection import Hand, Deck
from .interface import GameView, StartMenu, GameMenu

logger = settings.logging.getLogger("game")

@dataclass
class UnoGameConfig(GameConfig):
    stackable: bool = True
    effect_win: bool = True
    turn_time: float = 180
    min_players: int = 1
    max_players: int = 8

class UNOGame(BaseGame):
    def __init__(self, data: GameConfig) -> None:
        super().__init__(data)
        self.deck: Deck = Deck()
        self.graveyard: Deck = Deck()
        self.stack: int = 0
        self.last_action: str = "Game started with: "
        self.winner: Player
        self.emoji_collection: list[discord.Emoji]
        # self.thread: discord.Thread = data.thread

    async def get_emojis(self, ctx: discord.Client) -> list[discord.Emoji]:
        first_guild : discord.Guild = ctx.get_guild(892586895282958376)
        second_guild : discord.Guild = ctx.get_guild(892602982800162837)
        emoji_list: list[discord.Emoji] = []
        a = await first_guild.fetch_emojis()
        b = await second_guild.fetch_emojis()
        emoji_list.extend(a)
        emoji_list.extend(b)
        self.emoji_collection = emoji_list

    def start_game(self):
        if self.status != GameState.WAITING: return print("Game already started...")

        self.deck.generate_deck()
        # random.shuffle(self.deck.cards)

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
    
    def punish_user(self):
        if self.current_player.warns == 2:
            self.del_player(self.current_player)

            if len(self.players) == 1:
              self.status = GameState.CANCELLED
            return
                
        else:
            self.current_player.hand.add_card(self.deck.pop_card())
            self.current_player.hand.add_card(self.deck.pop_card())
            self.current_player.hand.add_card(self.deck.pop_card())
            self.current_player.warns += 1
            logger.info(f"User punished: {self.current_player.name} has {self.current_player.warns} warns")
            self.skip_turn()


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
    async def play_card(self, player: Player, card: int) -> Card | None:
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
            for x in range(1):
                player.hand.add_card(self.deck.pop_card())
    
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

"""
Clase involucrada en enviar mensajes, recibir comandos, hacer el manejo entero del juego usando la GameClass y
además va accionar en base a los resultados al final del juego.
"""
class Main:
    def __init__(self, ctx: discord.Interaction) -> None:
        self.ctx : discord.Interaction = ctx # First command interaction
        self.game : UNOGame = UNOGame(UnoGameConfig(owner=ctx.user, ctx=ctx.client))

    async def start(self):
        logger.info(f"UNO!: Game Started 💙")
        self.main_view : GameView = StartMenu(game=self.game)
        await self.game.get_emojis(self.ctx.client)
        await self.game_state_message() # ingresa al bucle

    async def game_state_message(self):
        if self.game.status == GameState.WAITING:
            # Juego no iniciado
            await self.main_menu_message(ctx=self.ctx, view=self.main_view)
            await self.main_view.wait()
        elif self.game.status == GameState.PLAYING:
            # Juego iniciado
            is_current_player_last_card:bool = len(self.game.current_player.hand.cards) == 1
            self.game_view = GameMenu(timeout=self.game.game_data_config.turn_time,game=self.game)
            await self.game_menu_message(ctx=self.ctx, view=self.game_view)
            turn = await self.game_view.wait()
            if turn: self.game.punish_user() # si turn devuelve true quiere decir que el jugador dejó pasar el tiempo
        else:
            # Juego terminado o cancelado
            await self.end_cycle()
            return
        await self.game_state_message()

    """
    Enviar resultado final
    """
    async def end_cycle(self):
        if self.game.status == GameState.CANCELLED:
            await self.ctx.channel.send("Game has been cancelled because si mucho muy.")
        else:
            await self.ctx.channel.send(f"The indiscutible ganer (o sea ganador) es {self.game.winner.name}")
        self.game = None

    async def main_menu_message(self, ctx: discord.Interaction, view: GameView):
        await ctx.response.defer()
        embed = discord.Embed(title="UNO Beta")
        embed.description = f"```markdown\n{self.game.player_list}```"
        embed.set_footer(text="If the game doesn't start in 10 minutes will be cancelled.")
        start_msg = await ctx.followup.send(embed=embed, view=view)
        view.msg = start_msg
        view.embed = embed

    async def game_menu_message(self, ctx: discord.Interaction, view: GameView):
        embed = discord.Embed(title="UNO Beta", color=self.game.graveyard.last_card.color_code, description=(
            f"{self.game.last_action + self.game.graveyard.last_card.name}\n"
            f"```markdown\n{self.game.player_list}```"
        ))
        embed.set_thumbnail(url=self.game.graveyard.last_card.image_url)
        embed.add_field(inline=True,name="Orientation:", value=f"{'⏬ Down' if self.game.is_clockwise else '⏫ Up'}")
        embed.add_field(inline=True,name="Stack:", value=f"{self.game.stack}")
        await ctx.channel.send(content=f"<@{self.game.current_player.id}>'s turn", embed=embed, view=view)