import discord
import settings
from typing import List
from discord.emoji import Emoji
from discord.enums import ButtonStyle
from discord.partial_emoji import PartialEmoji
from game_base import GameState, GameBase
from .card import UnoCard


logger = settings.logging.getLogger("game")

class GameView(discord.ui.View):    
    def __init__(self, *, timeout: float | None = 180, game):
        super().__init__(timeout=timeout)
        self.game : GameBase = game

    async def disable_all_items(self, interaction: discord.Interaction):
        for item in self.children:
            item.disabled = True
        await interaction.original_response.edit(view=self)

class StartMenu(GameView):

    msg: discord.Message | discord.WebhookMessage
    embed: discord.Embed

    async def on_timeout(self):
        self.game.status = GameState.CANCELLED
        logger.info("UNO HAS BEEN CANCELEITED")

    @discord.ui.button(label="Start", style=discord.ButtonStyle.primary, custom_id="start")
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if interaction.user.id != self.game.game_data_config.owner.id:
            # TODO: esto figura como que ya está respondido por el defer anterior
            await interaction.followup.send(content="> You cannot start this game.", ephemeral=True, wait=False)
            return
        else:
            await self.msg.edit(view=None)
            self.game.start_game()
            self.stop()
        
    @discord.ui.button(label="Join", style=discord.ButtonStyle.primary, custom_id="join")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(content=f"> {self.game.add_player(user=interaction.user)}", ephemeral=True)
        # if self.game.get_player_by_id(interaction.user.id) != None: return
        self.embed.description = (
            "Join and play UNO!"
            f"```markdown\n{self.game.player_list}```"
        )
        await self.msg.edit(embed=self.embed, view=self)

class WildMenu(discord.ui.View):
    def __init__(self, *, timeout: float | None = 180, card: UnoCard):
        super().__init__(timeout=timeout)
        self.card = card

    async def on_timeout(self):
        self.card.color = "R"

    @discord.ui.button(emoji="🔴", custom_id="R")
    async def red(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.card.color = "R"
        self.stop()

    @discord.ui.button(emoji="🟡", custom_id="Y")
    async def yellow(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.card.color = "Y"
        self.stop()

    @discord.ui.button(emoji="🔵", custom_id="B")
    async def blue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.card.color = "B"
        self.stop()

    @discord.ui.button(emoji="🟢", custom_id="G")
    async def green(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.card.color = "G"
        self.stop()

class StackDrawItem(discord.ui.Button):
    def __init__(self, *, style: ButtonStyle = ButtonStyle.secondary, label: str | None = None, disabled: bool = False, custom_id: str | None = None, url: str | None = None, emoji: str | Emoji | PartialEmoji | None = None, row: int | None = None, game):
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)
        self.game = game

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.game.current_player.id: return await interaction.response.send_message(content="It's not your turn", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        self.game.stack_resolve()
        self.view.stop()

class CardSelectItem(discord.SelectOption):
    ...

class CardSelectView(discord.ui.Select):
    def __init__(self, *, custom_id: str = ..., placeholder: str | None = None, min_values: int = 1, max_values: int = 1, options: List[discord.SelectOption] = ..., disabled: bool = False, row: int | None = None, cards: list[UnoCard], game: GameBase) -> None:
        super().__init__(custom_id=custom_id, placeholder=placeholder, min_values=min_values, max_values=max_values, options=options, disabled=disabled, row=row)
        self.cards: list[UnoCard] = cards
        self.game: GameBase = game
        for card in cards:
            item = CardSelectItem(label=f"{card.name}", value=f"{card.id}", emoji=card.color_emoji)
            self.append_option(option=item)

    # send the card item value to the game, the game will search for the card in the hand and send it to graveyard.
    async def callback(self, interaction: discord.Interaction):
        card_id = interaction.data.get('values')[0]
        player = self.game.get_player_by_id(interaction.user.id)
        the_actual_card=player.hand.get_card_by_id(card_id)

        if(the_actual_card.is_wild):
            wild_view = WildMenu(timeout=60, card=the_actual_card)
            await interaction.response.send_message(content="> Select a new color, you have 60 seconds.", view=wild_view, ephemeral=True)
            await wild_view.wait()

        card: UnoCard | None = await self.game.play_card(player, card_id)
        self.view.stop()


class CardSelect(GameView):
    def __init__(self, *, timeout: float | None = 180, game, game_view: GameView, card_list: list[UnoCard] | None):
        super().__init__(timeout=timeout, game=game)
        self.game_view: GameView = game_view
        self.card_list = card_list
    
    async def generate_hand(self):
        if self.card_list == None: return
        valid_hand = CardSelectView(custom_id="send_card", cards=self.card_list, options=[], game=self.game)
        self.add_item(valid_hand)

    """Chequea si es turno del usuario que interactuó"""
    async def interaction_check(self, interaction: discord.Interaction):
        return self.game.players[self.game.current_player_index].id == interaction.user.id

        
class DrawSelectView(GameView):
    def __init__(self, *, timeout: float | None = 180, game, game_view: GameView, card: UnoCard):
        super().__init__(timeout=timeout, game=game)
        self.game_view: GameView = game_view
        self.card: UnoCard = card
    
    async def on_timeout(self):
        self.game.last_action = f"{self.game.players[self.game.current_player_index].name} picked up a card, the last card is: "
        self.game.skip_turn()

    @discord.ui.button(label="Throw")
    async def throw(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        # await interaction.response.send_message(content="> You sent the card", ephemeral=True)
        await self.game_view.draw_message.edit(view=None)
        await self.game.play_card(self.game.current_player, card=self.card.id)
        self.game.last_action = f"{self.game.current_player.name} picked up a card and threw it: "
        self.game_view.stop()
        self.stop()

    @discord.ui.button(label="Skip")
    async def keep(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        # await interaction.response.send_message(content="> You kept the card", ephemeral=True)
        await self.game_view.draw_message.edit(view=None)
        self.game.last_action = f"{self.game.players[self.game.current_player_index].name} picked up a card, the last card is: "
        self.game.skip_turn()
        self.game_view.stop()
        self.stop()

class GameMenu(GameView):
    def __init__(self, *, timeout: float | None = 180, game):
        super().__init__(timeout=timeout, game=game)
        self.card_select_view: CardSelectView | None = None
        self.draw_select_view: DrawSelectView | None = None
        self.hand_message: discord.WebhookMessage | None = None
    
    foo: bool = False

    async def on_timeout(self):
        if self.hand_message is not None: await self.hand_message.edit(view=None)
        if self.card_select_view != None: self.card_select_view.stop()
        if self.draw_select_view != None: self.draw_select_view.stop()

    """
    check player turn, if is not just give emoji cards
    """
    @discord.ui.button(label="Hand", style=discord.ButtonStyle.green, custom_id="hand")
    async def hand(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self.game.get_player_by_id(interaction.user.id) # obtain player from the list
        if player == self.game.players[self.game.current_player_index]:
            if self.hand_message is not None: await self.hand_message.edit(view=None)
            valid_hand = player.hand.generate_valid_hand(last_card=self.game.graveyard.last_card)
            emoji_hand = player.hand.emoji_hand(self.game.emoji_collection)

            if player.hand.last_card.is_wild and len(player.hand.cards) == 1:
                valid_hand = []

            if self.game.stack >= 2:
                valid_hand = player.hand.generate_plus_hand()

            # If player turn, give the hand and the actions.
            if len(valid_hand) == 0:
                # TODO: This approach doesn't work
                await interaction.response.defer(ephemeral=True)
                logger.info(f"{player.name} doesn't have valid cards to play.")
                self.hand_message = await interaction.followup.send(content=emoji_hand, ephemeral=True, wait=False)
            else:
                await interaction.response.defer(ephemeral=True)
                self.card_select_view = CardSelect(game=self.game, timeout=120, game_view=self, card_list=valid_hand)
                await self.card_select_view.generate_hand()
                self.hand_message = await interaction.followup.send(content=f"{emoji_hand}", ephemeral=True, wait=True, view=self.card_select_view)
                await self.card_select_view.wait()
                new_hand = player.hand.emoji_hand(self.game.emoji_collection)
                await self.hand_message.edit(content=new_hand, view=None)
                self.stop()
        else:
            player = self.game.get_player_by_id(interaction.user.id)
            await interaction.response.send_message(content=player.hand.emoji_hand(self.game.emoji_collection), ephemeral=True)

    """
    check player turn, if is not just return ephemeral message "it's' not your turn"
    """
    @discord.ui.button(label="Draw", style=discord.ButtonStyle.grey, custom_id="draw")
    async def draw(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.card_select_view != None: self.card_select_view.stop()
        if self.foo == True: return
        player = self.game.get_player_by_id(interaction.user.id)
        # check player turn
        if player == self.game.players[self.game.current_player_index]:
            if self.hand_message is not None: await self.hand_message.edit(view=None)
            card : UnoCard = await self.game.draw_card(player)
            if card.validate(self.game.graveyard.last_card) and not card.is_wild:
                logger.info(msg=f"UNO: Player can throw {card.name} ✅")
                self.foo = True
                await interaction.response.defer(ephemeral=True)
                self.draw_select_view = DrawSelectView(game=self.game, timeout=60, game_view=self, card=card)
                self.draw_message = await interaction.followup.send(content=f"> You picked up [`{card.name}`] {card.get_one_emoji(self.game.emoji_collection)}, you want to throw it?, you got 60 seconds.", ephemeral=True, wait=True, view=self.draw_select_view)
                await self.draw_select_view.wait()
            else:
                logger.info(msg=f"UNO: Player can't throw {card.name} 🚫")
                self.game.last_action = f"{player.name} picked up a card, the last card is: "
                await interaction.response.send_message(content=f"> You picked up [`{card.name}`] {card.get_one_emoji(self.game.emoji_collection)}", ephemeral=True)
                self.game.skip_turn()
            self.stop()
        else:
            await interaction.response.send_message(content="> It's not your turn, asshole.", ephemeral=True)
    
    """
    Chequea si el usuario que interactuó realmente está jugando.
    """
    async def interaction_check(self, interaction: discord.Interaction):
        player = self.game.get_player_by_id(interaction.user.id)
        if player not in self.game.players:
            await interaction.response.send_message("> You are not even playing, are you dumb?", ephemeral=True)
            return False
        else: return True