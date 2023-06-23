from typing import List, Optional
import discord
import settings
from ..base.base_game import BaseGame
from .card import Card, CardFilter

logger = settings.logging.getLogger("game")

class GameView(discord.ui.View):    
    def __init__(self, *, timeout: float | None = 180, game):
        super().__init__(timeout=timeout)
        self.game : BaseGame = game

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
        self.embed.description = (
            "Join and play UNO!"
            f"```markdown\n{self.game.player_list}```"
        )
        await self.msg.edit(embed=self.embed, view=self)

class WildMenu(discord.ui.View):
    def __init__(self, *, timeout: float | None = 180, card: Card):
        super().__init__(timeout=timeout)
        self.card = card

    def on_timeout(self):
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


class CardSelectItem(discord.SelectOption):
    ...

class CardSelectMenu(discord.ui.Select):
    def __init__(self, *, custom_id: str = ..., placeholder: str | None = None, min_values: int = 1, max_values: int = 1, options: List[discord.SelectOption] = ..., disabled: bool = False, row: int | None = None, cards: list[Card], game: BaseGame) -> None:
        super().__init__(custom_id=custom_id, placeholder=placeholder, min_values=min_values, max_values=max_values, options=options, disabled=disabled, row=row)
        self.cards: list[Card] = cards
        self.game: BaseGame = game
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
            await interaction.response.send_message(content="Select a new color", view=wild_view, ephemeral=True)
            await wild_view.wait()

        card: Card | None = await self.game.play_card(player, card_id)
        self.view.stop()


class CardSelect(GameView):
    def __init__(self, *, timeout: float | None = 180, game, game_view: GameView, card_list: list[Card] | None):
        super().__init__(timeout=timeout, game=game)
        self.game_view: GameView = game_view
        self.card_list = card_list
    
    async def generate_hand(self):
        if self.card_list == None: return print("This player doesn't have cards to throw")
        valid_hand = CardSelectMenu(custom_id="send_card", cards=self.card_list, options=[], game=self.game)
        self.add_item(valid_hand)

    """Chequea si es turno del usuario que interactuó"""
    async def interaction_check(self, interaction: discord.Interaction):
        return self.game.players[self.game.current_player_index].id == interaction.user.id

        
class DrawSelectView(GameView):
    def __init__(self, *, timeout: float | None = 180, game, game_view: GameView, card: Card):
        super().__init__(timeout=timeout, game=game)
        self.game_view: GameView = game_view
        self.card: Card = card
    
    """
    @TODO: Send card to game
    """
    @discord.ui.button(label="Throw")
    async def throw(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(content="You sent a card", ephemeral=True)
        await self.game_view.draw_message.edit(view=None)
        await self.game.play_card(self.game.current_player, card=self.card.id)
        self.game.last_action = f"{self.game.current_player.name} picked up a card and threw it: "
        self.game_view.stop()
        self.stop()

    @discord.ui.button(label="Skip")
    async def keep(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(content="You kept the card", ephemeral=True)
        await self.game_view.draw_message.edit(view=None)
        self.game.last_action = f"{self.game.players[self.game.current_player_index].name} picked up a card, the last card is: "
        self.game.skip_turn()
        self.game_view.stop()
        self.stop()

class GameMenu(GameView):
    def __init__(self, *, timeout: float | None = 180, game):
        super().__init__(timeout=timeout, game=game)
        self.card_select_view: GameView | None = None
        self.draw_select_view: DrawSelectView | None = None
        self.hand_message: discord.WebhookMessage | None = None
    
    foo: bool = False

    """
    check player turn, if is not just give emoji cards
    """
    @discord.ui.button(label="Hand", style=discord.ButtonStyle.green, custom_id="hand")
    async def hand(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self.game.get_player_by_id(interaction.user.id) # obtain player from the list
        if player == self.game.players[self.game.current_player_index]:
            if self.hand_message is not None: await self.hand_message.edit(view=None)
            hand = player.hand.generate_valid_hand(last_card=self.game.graveyard.last_card)
            emoji_hand = player.hand.emoji_hand(self.game.emoji_collection)

            if len(hand) == 0:
                # No tienes cartas para tirar
                await interaction.response.send_message(f"{emoji_hand}") # REPLACE WITH EMOJIS
            else:
                self.card_select_view = CardSelect(game=self.game, timeout=120, game_view=self, card_list=hand)
                await self.card_select_view.generate_hand()
                await interaction.response.defer(ephemeral=True)
                self.hand_message = await interaction.followup.send(content=f"{emoji_hand}", ephemeral=True, wait=True, view=self.card_select_view)
                await self.card_select_view.wait()
                new_hand = player.hand.emoji_hand(self.game.emoji_collection)
                await self.hand_message.edit(content=new_hand, view=None)
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
        # check player turn
        if player == self.game.players[self.game.current_player_index]:
            if self.hand_message is not None: await self.hand_message.edit(view=None)
            card = await self.game.draw_card(player)
            if card.validate(self.game.graveyard.last_card) and not card.is_wild:
                logger.info(msg=f"UNO: Player can throw {card.name} ✅")
                self.foo = True
                # TODO
                await interaction.response.defer(ephemeral=True)
                self.draw_select_view = DrawSelectView(game=self.game, timeout=120, game_view=self, card=card)
                self.draw_message = await interaction.followup.send(content=f"You picked up {card.name}, you want to throw it?", ephemeral=True, wait=True, view=self.draw_select_view)
                await self.draw_select_view.wait()
            else:
                logger.info(msg=f"UNO: Player can't throw {card.name} 🚫")
                self.game.last_action = f"{player.name} picked up a card, the last card is: "
                await interaction.response.send_message(content="You draw a card", ephemeral=True)
                self.game.skip_turn()
            self.stop()
        else:
            await interaction.response.send_message(content="It's not your turn, asshole.", ephemeral=True)
    
    """
    Chequea si el usuario que interactuó realmente está jugando.
    """
    async def interaction_check(self, interaction: discord.Interaction):
        player = self.game.get_player_by_id(interaction.user.id)
        if player not in self.game.players:
            await interaction.response.send_message("You are not even playing, are you dumb?")
            return False
        else: return True