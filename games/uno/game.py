import asyncio
import random
from threading import Timer
from typing import Optional
import discord
from discord import Member
import settings
from dataclasses import dataclass

# game imports
from game_base import *
from utils.to_thread import to_thread
from .card_collection import UnoHand, UnoDeck
from .card import UnoCard
from .interface import GameView, StartMenu, PlayingView, StackDrawItem

logger = settings.logging.getLogger("game")

@dataclass
class UnoGameConfig(GameConfig):
    stackable: bool = True
    effect_win: bool = True
    randomize_players: bool = False
    turn_time: float = 180

class UnoPlayer(Player):
    def __init__(self, user: discord.Member) -> None:
        super().__init__(user)
        self.hand: UnoHand = UnoHand()

class UNOGame(GameBase):
    def __init__(self, data: GameConfig) -> None:
        super().__init__(data)
        self.emoji_collection: list[discord.Emoji]
        self.thread: discord.Thread = None
        self.msg_handler: GameMessageHandler = GameMessageHandler(self)
        self.players: list[UnoPlayer] = []
        self.deck: UnoDeck = UnoDeck()
        self.graveyard: UnoDeck = UnoDeck()
        self.winner: Player | None = None
        self.last_action: str = "Game started with: "
        self.stack: int = 0
        self.timer : Timer | None = None
        self.player_turn_view: PlayerTurnView = None

    async def get_emojis(self) -> list[discord.Emoji]:
        first_guild : discord.Guild = self.data.client.get_guild(892586895282958376)
        second_guild : discord.Guild = self.data.client.get_guild(892602982800162837)
        emoji_list: list[discord.Emoji] = []
        a = await first_guild.fetch_emojis()
        b = await second_guild.fetch_emojis()
        emoji_list.extend(a)
        emoji_list.extend(b)
        self.emoji_collection = emoji_list

    async def add_player(self, user: Member) -> str:
        # check if can add
        if self.status == GameState.PLAYING: return f"Can't add a player while the game is running..."
        if user.id in [p.id for p in self.players]: return f"You are already in the game..."
        if len(self.players) == self.data.max_players: return f"Maximum players: {self.data.max_players}"

        self.players.append(UnoPlayer(user))
        return f"{user.display_name} joined the game succesfully."

    def start_game(self):
        if self.status != GameState.WAITING: raise Exception("Game already started...")
        if len(self.players) < self.data.min_players: raise Exception(f"Minimum of players is {self.data.min_players}")

        if self.data.randomize_players: self.randomize_players()

        self.deck.generate_deck()
        random.shuffle(self.deck.cards)

        self.deal_cards()

        while(self.deck.last_card.is_wild):
            random.shuffle(self.deck.cards)
        
        self.graveyard.add_card(self.deck.pop_card())

        self.status = GameState.PLAYING
        self.set_turn_timer()

    """
    Changes the current_index value, can't be higher than the length of the players list.
    If is_clockwise current_index value will cycle reversed.
    """
    async def skip_turn(self):
        print("Skip turn")
        if self.is_clockwise:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
        else:
            self.current_player_index = (self.current_player_index - 1 + len(self.players)) % len(self.players)

        self.set_turn_timer()
        await self.msg_handler.send_status_message()
        self.check_win()
    
    async def punish_user(self):
        self.last_action = f"{self.current_player.name} lose his turn and eat 3 cards, last card is: " if self.stack == 0 else f"{self.current_player.name} lose his turn and eat 3 cards plus {self.stack} stacked cards, last card is: "
        if self.current_player.warns == 2:
            self.del_player(self.current_player)

            if len(self.players) == 1:
              self.status = GameState.CANCELLED
        else:
            self.current_player.hand.add_multiple_cards(self.deck.pop_multiple_cards(3))
            self.current_player.warns += 1
            if self.stack >= 1: await self.stack_resolve(skip=False)
            logger.info(f"User punished: {self.current_player.name} has {self.current_player.warns} warns")
            await self.skip_turn()

    def set_turn_timer(self):
        self.timer = Timer(self.data.turn_time, self.on_turn_timeout)
        self.timer.start()

    def on_turn_timeout(self):
        self.punish_user()
        if self.player_turn_view is not None:
            self.player_turn_view.stop()
            self.player_turn_view = None

    def check_win(self):
        if len(self.current_player.hand.cards) == 0:
            self.status = GameState.FINISHED
            self.winner = self.current_player
            self.timer.cancel()
    
    def change_orientation(self):
        self.is_clockwise = not self.is_clockwise

    async def stack_resolve(self, skip: bool = True):
        self.current_player.hand.add_multiple_cards(self.deck.pop_multiple_cards(self.stack))
        self.stack = 0
        if skip: await self.skip_turn()
            

    """
    Juega la carta seleccionada
    """
    async def play_card(self, player: Player, card: int) -> UnoCard | None:
        if player is not self.current_player: return None
        card: UnoCard = player.hand.get_card_by_id(card)
        if card == None: return print("ERROR: Card doesn't exist")

        print("Play card")

        if card.has_effect or card.value == "+4":
            card.effect.execute(game=self)

        # play process
        player.hand.del_card(card)
        self.last_action = f"{player.name} sent a card: "
        self.graveyard.add_card(card)
        await self.skip_turn()

        return card
    
    """
    Levanta una carta y retorna la carta levantada.
    """
    async def draw_card(self, player: Player) -> UnoCard:
        card = self.deck.pop_card()
        player.hand.add_card(card)
        return card

    """
    Deal 7 cards for each player in the list.
    """
    def deal_cards(self):
        for player in self.players:
            player.hand.add_multiple_cards(self.deck.pop_multiple_cards(7))
    
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
    
    @property
    def next_player(self) -> Player:
        if self.is_clockwise:
            return self.players[(self.current_player_index + 1) % len(self.players)]
        else:
            return self.players[(self.current_player_index - 1 + len(self.players)) % len(self.players)]

    @property
    def last_card(self) -> Card:
        return self.graveyard.last_card

###################################################################################################
class PlayerTurnView(discord.ui.View):

    is_played: bool = False

    def __init__(self, *, timeout: float | None = 180, game):
        super().__init__(timeout=timeout)
        self.game: UNOGame = game
        self.msg: discord.WebhookMessage = None
        self.generate_hand()
    
    def generate_hand(self):
        valid_hand = self.game.current_player.hand.generate_valid_hand(self.game.last_card)
        if self.game.stack > 0:
            # genera la mano de +2
            ...
        elif len(self.game.current_player.hand.cards) != 0:
            card_select_menu = discord.ui.Select(custom_id="send_card", options=[])
            for card in valid_hand:
                item = discord.SelectOption(label=f"{card.name}", value=card.id, emoji=card.color_emoji)
                card_select_menu.append_option(item)
            self.add_item(card_select_menu)

    @discord.ui.button(label="Draw")
    async def draw_card(self, interaction: discord.Interaction, button):
        card = await self.game.draw_card(self.game.current_player)
        print(f"{self.game.current_player.name} picked up {card.name}")
        if card.validate(self.game.last_card) and not card.is_wild:
            # you may throw it
            await self.game.skip_turn()
        else:
            print('\nand keep it')
            self.is_played = True
            self.game.last_action = f"{self.game.current_player.name} picked up a card, last card is: "
            await self.game.skip_turn()
        self.stop()


########### GAME MESSAGE HANDLER:
class HandButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        game: UNOGame = self.view.game
        player: UnoPlayer = game.get_player_by_id(interaction.user.id)
        if player is None: return await interaction.response.send_message(content="You're not even playing...", ephemeral=True)
        if self.view.game.current_player == player:
            await interaction.response.defer()
            # valid_hand = player.hand.generate_valid_hand(game.last_card)
            game.player_turn_view: PlayerTurnView = PlayerTurnView(game=game) # view con selector de cartas
            hand_message = await interaction.followup.send(content=f"{player.hand.emoji_hand(game.emoji_collection)}", view=game.player_turn_view, ephemeral=True)
            game.player_turn_view.msg = hand_message
            await game.player_turn_view.wait()
            game.player_turn_view = None
        else:
            # genera mensaje con la mano
            await interaction.response.send_message(content=f"{player.hand.emoji_hand(game.emoji_collection)}", ephemeral=True)

class GamePlayView(discord.ui.View):
    def __init__(self, *, timeout: float | None = 180, game):
        super().__init__(timeout=None)
        self.game: GameBase = game
        self.add_item(HandButton(label="Hand", custom_id="hand", style=discord.ButtonStyle.blurple))

class GameMessageHandler: 
    def __init__(self, game: GameBase) -> None:
        self.game: GameBase = game
        self.options: discord.ui.View = GamePlayView(game=game)

    async def send_status_message(self):
        await self.game.data.thread.send(content=f"# La carta del top es: {self.game.last_card.name}\n{self.game.player_list}", view=self.options)
    
###################################################################################################
### Views:
class StartMenuView(discord.ui.View):
    foo: bool | None = None

    def __init__(self, *, timeout: float | None = 180, game):
        super().__init__(timeout=timeout)
        self.game : UNOGame = game

    async def on_timeout(self):
        print("Juego nunca comenzó, cancelado.")
    
    @discord.ui.button(label="Start", custom_id="start")
    async def start_button(self, interaction: discord.Interaction, button):
        if interaction.user.id == self.game.players[0].id:
            self.game.start_game()
            await self.game.get_emojis()
            await self.game.msg_handler.send_status_message()
            self.stop()

    @discord.ui.button(label="Join", custom_id="join", style=discord.ButtonStyle.green)
    async def join_button(self, interaction: discord.Interaction, button):
        await self.game.add_player(interaction.user)
        await interaction.response.edit_message(content=self.game.player_list)

class GameManager:
    def __init__(self, ctx: discord.Interaction) -> None:
        self.game: UNOGame = UNOGame(data=UnoGameConfig(client=ctx.client, thread=ctx.channel))

    async def start_menu_func(self, interaction: discord.Interaction):
        self.game_msg_handler = GameMessageHandler(self.game)
        await self.game.add_player(interaction.user)

        start_menu_view: discord.ui.View = StartMenuView(timeout=60, game=self.game)
        await interaction.edit_original_response(content=self.game.player_list, view=start_menu_view)

        await start_menu_view.wait()


""" @DEPRECATED
Clase involucrada en enviar mensajes, recibir comandos, hacer el manejo entero del juego usando la GameClass y
además va accionar en base a los resultados al final del juego.
"""
# class Main:
#     def __init__(self, ctx: discord.Interaction, randomize) -> None:
#         self.ctx : discord.Interaction = ctx # First command interaction
#         self.game : UNOGame = UNOGame(UnoGameConfig(owner=ctx.user, client=ctx.client, randomize_players=randomize))

#     async def start(self):
#         logger.info(f"UNO!: Game Started 💙")
#         self.main_view : GameView = StartMenu(timeout=600,game=self.game)
#         await self.game.get_emojis(self.ctx.client)
#         await self.game_state_message() # ingresa al bucle

#     async def game_state_message(self):
#         if self.game.status == GameState.WAITING:
#             # Juego no iniciado
#             ...
#         elif self.game.status == GameState.PLAYING:
#             is_current_player_last_card:bool = len(self.game.current_player.hand.cards) == 1
#             self.game_view = PlayingView(timeout=self.game.data.turn_time,game=self.game)

#             ### Check Stackable
#             if self.game.data.stackable and self.game.stack > 0:
#                 self.game_view.remove_item(self.game_view.children[1])
#                 self.game_view.add_item(StackDrawItem(label=f"Draw {self.game.stack} cards", style=discord.ButtonStyle.danger, game=self.game))
#             elif not self.game.data.stackable and self.game.stack == 2:
#                 self.game.stack_resolve()

#             ### Await Turn ###
#             await self.game_menu_message(ctx=self.ctx, view=self.game_view)
#             turn = await self.game_view.wait()

#             ### If timeout
#             if turn: self.game.punish_user() # si turn devuelve true quiere decir que el jugador dejó pasar el tiempo
#         elif self.game.status == GameState.FINISHED or self.game.status == GameState.CANCELLED:
#             # Juego terminado o cancelado
#             await self.end_cycle()
#             return
#         else:
#             return
#         await self.game_state_message()

#     """
#     Enviar resultado final
#     """
#     async def end_cycle(self):
#         logger.info(f"UNO GAME FINISHED: {self.game.status.name}")
#         if self.game.status == GameState.CANCELLED or self.game.status == GameState.WAITING:
#             response = await self.ctx.original_response()
#             await response.delete()
#             await self.game.thread.delete()
#         elif self.game.status == GameState.FINISHED:
#             response = await self.ctx.original_response()
#             await response.delete()
#             await self.game.thread.delete()

#     async def thread_deleted(self):
#         logger.info(f"UNO GAME FINISHED CAUSE THE THREAD WAS DELETED")
#         self.game.status = GameState.NONE
#         await self.game_state_message()

#     async def main_menu_message(self, ctx: discord.Interaction, view: GameView):
#         embed = discord.Embed(title="UNO Beta")
#         embed.description = f"```markdown\n{self.game.player_list}```"
#         embed.set_footer(text="If the game doesn't start in 10 minutes will be cancelled.")
#         await ctx.response.send_message("Let's play UNO!")
#         response: discord.InteractionMessage = await ctx.original_response()
#         self.game.thread = await response.create_thread(name=f"UNO! {ctx.user.display_name}")
#         view.msg = await self.game.thread.send(embed=embed, view=view)
#         view.embed = embed
#         ctx.client.games[ctx.guild_id] = self
        
#     async def game_menu_message(self, ctx: discord.Interaction, view: GameView):
#         embed = discord.Embed(title="UNO Beta", color=self.game.graveyard.last_card.color_code, description=(
#             f"Join and play UNO!\n{self.game.last_action + self.game.graveyard.last_card.name}\n"
#             f"```markdown\n{self.game.player_list}```"
#         ))
#         embed.set_thumbnail(url=self.game.graveyard.last_card.image_url)
#         embed.add_field(inline=True,name="Orientation:", value=f"{'⏬ Down' if self.game.is_clockwise else '⏫ Up'}")
#         embed.add_field(inline=True,name="Stack:", value=f"{self.game.stack}")
#         await self.game.thread.send(content=f"<@{self.game.current_player.id}>'s turn", embed=embed, view=view)