import random
import discord
import settings
from dataclasses import dataclass

# game imports
from game_base import *
from .card_collection import UnoHand, UnoDeck
from .card import UnoCard
from .game_message_handler import *

logger = settings.logging.getLogger("game")

@dataclass
class UnoGameConfig(GameConfig):
    stackable: bool = True
    effect_win: bool = True
    randomize_players: bool = False
    turn_time: float = 20

class UnoPlayer(Player):
    def __init__(self, user: discord.Member) -> None:
        super().__init__(user)
        self.hand: UnoHand = UnoHand()

class UNOGame(GameBase):
    def __init__(self, data: GameConfig) -> None:
        super().__init__(data)
        self.emoji_collection: list[discord.Emoji]
        self.thread: discord.Thread = self.data.thread
        self.players: list[UnoPlayer] = []
        self.deck: UnoDeck = UnoDeck()
        self.graveyard: UnoDeck = UnoDeck()
        self.winner: UnoPlayer | None = None
        self.last_action: str = "Game started with: "
        self.last_player: UnoPlayer | None = None
        self.stack: int = 0
        self.message_handler: GameDiscordInterface = GameDiscordInterface(self)

    async def get_emojis(self) -> list[discord.Emoji]:
        first_guild : discord.Guild = self.data.client.get_guild(892586895282958376)
        second_guild : discord.Guild = self.data.client.get_guild(892602982800162837)
        emoji_list: list[discord.Emoji] = []
        a = await first_guild.fetch_emojis()
        b = await second_guild.fetch_emojis()
        emoji_list.extend(a)
        emoji_list.extend(b)
        self.emoji_collection = emoji_list
        logger.info("Emoji cards added to the game...")

    async def add_player(self, user: Member) -> str:
        # check if can add
        if self.status == GameState.PLAYING: return f"Can't add a player while the game is running..."
        if user.id in [p.id for p in self.players]: return f"You are already in the game..."
        if len(self.players) == self.data.max_players: return f"Maximum players: {self.data.max_players}"

        self.players.append(UnoPlayer(user))
        return f"{user.display_name} joined the game succesfully."

    def start_game(self):
        if self.status != GameState.WAITING: return "Game already started..."
        if len(self.players) < self.data.min_players: return f"Minimum of players is {self.data.min_players}"
        if self.data.randomize_players: self.randomize_players()

        self.deck.generate_deck()
        random.shuffle(self.deck.cards)

        self.deal_cards()

        # add last card of the deck in the graveyard
        while(self.deck.last_card.is_wild):
            random.shuffle(self.deck.cards)
        self.graveyard.add_card(self.deck.pop_card())

        # change status
        self.last_player = self.current_player
        self.status = GameState.PLAYING
        logger.info(f"UNO Game started in the guild: {self.thread.guild.id}")
        return "Game started succesfully!"

    def skip_turn(self):
        logger.info("Turn skipped")

        self.last_player = self.current_player

        if self.is_clockwise:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
        else:
            self.current_player_index = (self.current_player_index - 1 + len(self.players)) % len(self.players)

        self.check_win()
    
    async def punish_user(self):
        self.last_action = f"{self.current_player.name} lose his turn and eat 3 cards, last card is: " if self.stack == 0 else f"{self.current_player.name} lose his turn and eat 3 cards plus {self.stack} stacked cards, last card is: "
        if self.current_player.warns == 2:
            logger.info(f"{self.current_player.name} recieved his last warn and got kicked out of the game.")
            self.del_player(self.current_player)

            if len(self.players) == 1:
              self.status = GameState.CANCELLED
              logger.info("Game cancelled due the lack of players.")
        else:
            self.current_player.hand.add_multiple_cards(self.deck.pop_multiple_cards(3))
            self.current_player.warns += 1
            if self.stack >= 1: await self.stack_resolve(force_skip=False)
            logger.info(f"User punished: {self.current_player.name} has {self.current_player.warns} warns")
            self.skip_turn()

    def check_win(self):
        if len(self.current_player.hand.cards) == 0:
            self.status = GameState.FINISHED
            self.winner = self.current_player
            self.timer.cancel()
    
    def change_orientation(self):
        self.is_clockwise = not self.is_clockwise

    async def stack_resolve(self, force_skip: bool = True):
        self.current_player.hand.add_multiple_cards(self.deck.pop_multiple_cards(self.stack))
        self.stack = 0
        if force_skip: self.skip_turn()
            
    def play_card(self, player: Player, card_id: int, force_skip: bool = True) -> UnoCard | None:
        if player is not self.current_player: return None
        card: UnoCard = player.hand.get_card_by_id(card_id)
        if card_id == None: return print("ERROR: Card doesn't exist")

        if card.has_effect or card.value == "WILD+4":
            card.effect.execute(game=self)

        # play process
        player.hand.del_card(card)
        self.last_action = f"{player.name} sent a card: "
        self.graveyard.add_card(card)
        logger.info(f"{player.name} played a card: {card.name}")

        if force_skip: self.skip_turn() 

        return card
    
    def draw_card(self, player: Player) -> UnoCard:
        card = self.deck.pop_card()
        player.hand.add_card(card)
        return card

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

class StartMenuView(discord.ui.View):
    foo: bool | None = None

    def __init__(self, *, timeout: float | None = 180, game):
        super().__init__(timeout=timeout)
        self.game : UNOGame = game

    async def on_timeout(self):
        print("Juego nunca comenzó, cancelado.")
        # do the thing...
    
    @discord.ui.button(label="Start", custom_id="start")
    async def start_button(self, interaction: discord.Interaction, button):
        if interaction.user.id == self.game.players[0].id:
            self.game.start_game()

            FIRST_VIEW = await self.game.message_handler.create_new_menu(HandButton(label="Hand", custom_id="hand_button"))
            GAME_START_EMBED.set_author(name="<< GAME STARTED >>")

            await interaction.response.edit_message(embed=GAME_START_EMBED,view=None)
            await self.game.get_emojis()
            await self.game.message_handler.send_status_message(view=FIRST_VIEW)
            self.stop()

    @discord.ui.button(label="Join", custom_id="join", style=discord.ButtonStyle.green)
    async def join_button(self, interaction: discord.Interaction, button):
        if interaction.user.id == self.game.players[0].id: return await interaction.response.send_message("Are you dumb?", ephemeral=True)
        await self.game.add_player(interaction.user)
        GAME_START_EMBED.description = (
            "Join UNO and beat your friend's ass."
            f"```md\n{self.game.player_list}```"
        )
        await interaction.response.edit_message(embed=GAME_START_EMBED)

class GameManager:
    def __init__(self, ctx: discord.Interaction) -> None:
        self.game: UNOGame = UNOGame(data=UnoGameConfig(client=ctx.client, thread=ctx.channel, turn_time=400))

    async def start_menu_func(self, interaction: discord.Interaction):
        # add the owner player:
        await self.game.add_player(interaction.user)

        # set embed player list
        GAME_START_EMBED.description = (
            "Join UNO and beat your friend's ass."
            f"```md\n{self.game.player_list}```"
        )

        # send the start menu
        start_menu_view: discord.ui.View = StartMenuView(timeout=60, game=self.game)
        await interaction.edit_original_response(embed=GAME_START_EMBED, view=start_menu_view)
        await start_menu_view.wait()