import random
from dataclasses import dataclass

import discord
from discord import Member

import settings

# game imports
from game_base import GameBase, GameConfig, GameState, Player

from .card import UnoCard
from .card_collection import UnoDeck, UnoHand
from .interface import GameView, PlayingView, StackDrawItem, StartMenu

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
        self.players: list[UnoPlayer] = [UnoPlayer(data.owner)]
        self.deck: UnoDeck = UnoDeck()
        self.graveyard: UnoDeck = UnoDeck()
        self.stack: int = 0
        self.last_action: str = "Game started with: "
        self.winner: Player | None = None
        self.emoji_collection: list[discord.Emoji]
        self.thread: discord.Thread = None

    async def get_emojis(self, ctx: discord.Client) -> list[discord.Emoji]:
        first_guild: discord.Guild = ctx.get_guild(892586895282958376)
        second_guild: discord.Guild = ctx.get_guild(892602982800162837)
        emoji_list: list[discord.Emoji] = []
        a = await first_guild.fetch_emojis()
        b = await second_guild.fetch_emojis()
        emoji_list.extend(a)
        emoji_list.extend(b)
        self.emoji_collection = emoji_list

    def add_player(self, user: Member):
        # check if can add
        if self.status == GameState.PLAYING:
            return
        if user.id in [p.id for p in self.players]:
            return "You are already in the game..."
        if len(self.players) == self.game_data_config.max_players:
            return f"Maximum players: {self.game_data_config.max_players}"

        self.players.append(UnoPlayer(user))
        return f"{user.display_name} joined the game succesfully."

    def start_game(self):
        if self.status != GameState.WAITING:
            return logger.info("UNO Game already started...")
        if len(self.players) < self.game_data_config.min_players:
            return logger.info(f"Minimum of players is {self.game_data_config.min_players}")

        if self.game_data_config.randomize_players:
            self.randomize_players()

        self.deck.generate_deck()
        random.shuffle(self.deck.cards)

        self.deal_cards()

        while self.deck.last_card.is_wild:
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
        self.last_action = (
            f"{self.current_player.name} lose his turn and eat 3 cards, last card is: "
            if self.stack == 0
            else
            f"{self.current_player.name} lose his turn and eat 3 cards plus {self.stack} stacked cards, last card is: "
        )
        if self.current_player.warns == 2:
            self.del_player(self.current_player)

            if len(self.players) == 1:
                self.status = GameState.CANCELLED
            return
        else:
            self.current_player.hand.add_multiple_cards(self.deck.pop_multiple_cards(3))
            self.current_player.warns += 1
            if self.stack >= 1:
                self.stack_resolve(skip=False)
            logger.info(f"User punished: {self.current_player.name} has {self.current_player.warns} warns")
            self.skip_turn()

    def check_win(self):
        if len(self.current_player.hand.cards) == 0:
            self.status = GameState.FINISHED
            self.winner = self.current_player

    def change_orientation(self):
        self.is_clockwise = not self.is_clockwise

    def stack_resolve(self, skip: bool = True):
        self.current_player.hand.add_multiple_cards(self.deck.pop_multiple_cards(self.stack))
        self.stack = 0
        if skip:
            self.skip_turn()

    """
    Juega la carta seleccionada
    """

    async def play_card(self, player: Player, card: int) -> UnoCard | None:
        if player is not self.current_player:
            return None
        card: UnoCard = player.hand.get_card_by_id(card)
        if card is None:
            return print("ERROR: Card doesn't exist")

        if card.has_effect or card.value == "+4":
            card.effect.execute(game=self)

        # play process
        player.hand.del_card(card)
        self.last_action = f"{player.name} sent a card: "
        self.graveyard.add_card(card)
        self.skip_turn()

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
                    list += (
                        f"▶ {player.name} ({len(player.hand.cards)} "
                        f"{'cards' if len(player.hand.cards) != 1 else 'card'})\n"
                    )
                else:
                    list += (
                        f"- {player.name} ({len(player.hand.cards)} "
                        f"{'cards' if len(player.hand.cards) != 1 else 'card'})\n"
                    )
        return list

    @property
    def next_player(self) -> Player:
        if self.is_clockwise:
            return self.players[(self.current_player_index + 1) % len(self.players)]
        else:
            return self.players[(self.current_player_index - 1 + len(self.players)) % len(self.players)]


"""
Clase involucrada en enviar mensajes, recibir comandos, hacer el manejo entero del juego usando la GameClass y
además va accionar en base a los resultados al final del juego.
"""


class Main:
    def __init__(self, ctx: discord.Interaction, randomize) -> None:
        self.ctx: discord.Interaction = ctx  # First command interaction
        self.game: UNOGame = UNOGame(UnoGameConfig(owner=ctx.user, ctx=ctx.client, randomize_players=randomize))

    async def start(self):
        logger.info("UNO!: Game Started 💙")
        self.main_view: GameView = StartMenu(timeout=600, game=self.game)
        await self.game.get_emojis(self.ctx.client)
        await self.game_state_message()  # ingresa al bucle

    async def game_state_message(self):
        if self.game.status == GameState.WAITING:
            # Juego no iniciado
            await self.main_menu_message(ctx=self.ctx, view=self.main_view)
            wait = await self.main_view.wait()
            if wait:
                return await self.end_cycle()
        elif self.game.status == GameState.PLAYING:
            len(self.game.current_player.hand.cards) == 1
            self.game_view = PlayingView(timeout=self.game.game_data_config.turn_time, game=self.game)

            ### Check Stackable
            if self.game.game_data_config.stackable and self.game.stack > 0:
                self.game_view.remove_item(self.game_view.children[1])
                self.game_view.add_item(
                    StackDrawItem(
                        label=f"Draw {self.game.stack} cards", style=discord.ButtonStyle.danger, game=self.game
                    )
                )
            elif not self.game.game_data_config.stackable and self.game.stack == 2:
                self.game.stack_resolve()

            ### Await Turn ###
            await self.game_menu_message(ctx=self.ctx, view=self.game_view)
            turn = await self.game_view.wait()

            ### If timeout
            if turn:
                self.game.punish_user()  # si turn devuelve true quiere decir que el jugador dejó pasar el tiempo
        elif self.game.status == GameState.FINISHED or self.game.status == GameState.CANCELLED:
            # Juego terminado o cancelado
            await self.end_cycle()
            return
        else:
            return
        await self.game_state_message()

    """
    Enviar resultado final
    """

    async def end_cycle(self):
        logger.info(f"UNO GAME FINISHED: {self.game.status.name}")
        if self.game.status == GameState.CANCELLED or self.game.status == GameState.WAITING:
            response = await self.ctx.original_response()
            await response.delete()
            await self.game.thread.delete()
        elif self.game.status == GameState.FINISHED:
            response = await self.ctx.original_response()
            await response.delete()
            await self.game.thread.delete()

    async def thread_deleted(self):
        logger.info("UNO GAME FINISHED CAUSE THE THREAD WAS DELETED")
        self.game.status = GameState.NONE
        await self.game_state_message()

    async def main_menu_message(self, ctx: discord.Interaction, view: GameView):
        embed = discord.Embed(title="UNO Beta")
        embed.description = f"```markdown\n{self.game.player_list}```"
        embed.set_footer(text="If the game doesn't start in 10 minutes will be cancelled.")
        await ctx.response.send_message("Let's play UNO!")
        response: discord.InteractionMessage = await ctx.original_response()
        self.game.thread = await response.create_thread(name=f"UNO! {ctx.user.display_name}")
        view.msg = await self.game.thread.send(embed=embed, view=view)
        view.embed = embed
        ctx.client.games[ctx.guild_id] = self

    async def game_menu_message(self, ctx: discord.Interaction, view: GameView):
        if not self.game.thread:
            return
        embed = discord.Embed(
            title="UNO Beta",
            color=self.game.graveyard.last_card.color_code,
            description=(
                f"{self.game.last_action + self.game.graveyard.last_card.name}\n"
                f"```markdown\n{self.game.player_list}```"
            ),
        )
        embed.set_thumbnail(url=self.game.graveyard.last_card.image_url)
        embed.add_field(inline=True, name="Orientation:", value=f"{'⏬ Down' if self.game.is_clockwise else '⏫ Up'}")
        embed.add_field(inline=True, name="Stack:", value=f"{self.game.stack}")
        await self.game.thread.send(content=f"<@{self.game.current_player.id}>'s turn", embed=embed, view=view)
