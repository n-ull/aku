from math import floor
import random
import discord
from game_base import GameBase
from typing import Tuple

# from games.uno.game import UNOGame

######## EMBEDS ##########

GAME_START_EMBED = discord.Embed().set_author(name="<< UNO GAME NOT STARTED >>")
GAME_STATUS_EMBED = discord.Embed().set_author(name="<< UNO GAME STATE MESSAGE>>")

##########################

class DrawOrThrowView(discord.ui.View):
    foo: bool = False

    @discord.ui.button(label="Throw")
    async def throw_button(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        self.foo = True
        self.stop()

    @discord.ui.button(label="Keep")
    async def keep_button(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        self.stop()
    

class CardSelector(discord.ui.Select):

    async def callback(self, interaction: discord.Interaction):
        card_id = interaction.data.get('values')[0]
        card = self.view.game.current_player.hand.get_card_by_id(card_id)
        player = self.view.game.get_player_by_id(interaction.user.id)
        # check if card is wild and wait for selection
        if card.is_wild:
            colors = ["R", "Y", "G", "B"] # select a random color if the player doesn't select
            card.color = random.choice(colors)
            

        # play card
        self.view.game.play_card(player, card_id)

        # close turn options view
        await self.view.close_view()

class DrawButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        # if custom id stack resolve, resolve stack...
        if interaction.data.get('custom_id') == "stack_resolve":
            self.view.game.stack_resolve()
        else:
            # grab a card
            card = self.view.game.draw_card(self.view.game.current_player)
            if card.validate(self.view.game.last_card) and not card.is_wild:
            # if can be played make second action true, and wait
                self.view.second_action = True
                self.children_view = DrawOrThrowView(timeout=60)
                await interaction.response.send_message(content=f"Do you want to keep `[{card.name}]` {card.emoji} or play it?", ephemeral=True, view= self.children_view)
                await self.children_view.wait()
                self.view.second_action = False

                if self.children_view.foo:
                    self.view.game.play_card(self.view.game.current_player, card.id, False)

        # if not just pass and close the view
        self.view.game.skip_turn()
        await self.view.close_view()

class TurnOptionsView(discord.ui.View):
    def __init__(self, *, timeout: float | None = None, game: GameBase, mother_view):
        super().__init__(timeout=timeout)
        self.ephemeral_message: discord.WebhookMessage = None
        # self.game : UNOGame = None # TODO: delete the typing when testing
        self.game = game
        self.second_action : bool = False
        self.mother_view: discord.ui.View = mother_view
        self.children_view: discord.ui.View | None = None

    # concludes the turn and send a new turn message
    async def close_view(self):
        # edit ephemeral message with new content? for draw and reflect the changes on your hand
        await self.ephemeral_message.edit(content=f"{self.game.last_player.hand.emoji_hand(self.game.emoji_collection)}",view=None)
        if self.ephemeral_message is not None: self.ephemeral_message = None # deletes the hand message webhook
        if self.children_view is not None: self.children_view = None # stop children view in case of a second option
        self.mother_view.last_hand_msg = None
        self.mother_view.opened = False
        await self.game.message_handler.send_status_message(view=self.mother_view)
        self.stop()
    
    def build_turn_menu(self):
        valid_hand = []
        # check if player has valid hand and then add card select menu
        # delete wild options in card selector if is the last card or there's a stack
        if self.game.stack > 0 and self.game.data.stackable:
            valid_hand = self.game.current_player.hand.generate_plus_hand()
        else:
            valid_hand = self.game.current_player.hand.generate_valid_hand(self.game.last_card)

        # if valid hand has items, make the select menu and append
        if len(valid_hand) > 0:
            card_selector: CardSelector = CardSelector(custom_id="send_card", options=[])
            for card in valid_hand:
                    card_selector.append_option(discord.SelectOption(label=card.name, emoji=card.color_emoji, value=card.id))
            self.add_item(card_selector)

        # check if there's an stack
        # with this make the draw button differente (draw x cards and red)
        if self.game.stack > 0 and self.game.data.stackable:
            self.add_item(DrawButton(label=f"Draw {self.game.stack} cards", style=discord.ButtonStyle.danger, custom_id="stack_resolve"))
        else:
            # add draw button
            self.add_item(DrawButton(label="Draw"))
        return self


class HandButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        print("This is the hand button")
        self.game = self.view.game
        player = self.game.get_player_by_id(interaction.user.id) # the player who touched the button
        player_emoji_hand = player.hand.emoji_hand(self.view.game.emoji_collection)

        # checks if it's not player's turn:
        if self.game.current_player.id != interaction.user.id:
            await interaction.response.send_message(content=player_emoji_hand, ephemeral=True)

        # is the player turn
        else:
            # checks if hand has been opened before:
            if self.view.opened:
                # edit the last hand message
                await self.view.last_hand_msg.edit(content=player_emoji_hand, view=None)

            if self.view.TURN_VIEW is not None:
                if self.view.TURN_VIEW.second_action: return await interaction.response.send_message("You've already make your choice...", ephemeral=True)

            # remember the hand button:
            await interaction.response.defer(ephemeral=True)
            self.view.TURN_VIEW = TurnOptionsView(timeout=self.game.data.turn_time, game=self.game, mother_view=self.view).build_turn_menu()

            self.view.opened = True
            self.view.last_hand_msg = await interaction.followup.send(content=player_emoji_hand, ephemeral=True, view=self.view.TURN_VIEW)
            self.view.TURN_VIEW.ephemeral_message = self.view.last_hand_msg

class PlayerTurnView(discord.ui.View):
    # Si el turno del jugador termina...
    async def on_timeout(self):
        self.clean_hand_message()
        await self.game.punish_user()

    async def clean_hand_message(self):
        # Si el jugador ya abrió su mano:
        if self.turn_options_view is not None:
            await self.turn_options_view.close_view()

    def __init__(self, *, timeout: float | None = 180, game: GameBase):
        super().__init__(timeout=timeout)
        self.game = game
        self.last_hand_msg : discord.WebhookMessage | None = None
        self.opened: bool = False # this will remember if the player used the button inside the view.
        self.TURN_VIEW = None

    async def interaction_check(self, interaction: discord.Interaction):
        # Revisar si el usuario se encuentra en el juego
        player = self.game.get_player_by_id(interaction.user.id)
        if player not in self.game.players:
            await interaction.response.send_message("> You are not even playing, are you dumb?", ephemeral=True)
            return False
        else: return True
        

class GameDiscordInterface:
    def __init__(self, game: GameBase) -> None:
        self.game = game
        self.thread : discord.TextChannel = game.thread # change to discord.Thread
    
    async def send_status_message(self, view: discord.ui.View | None = None):
        GAME_STATUS_EMBED.description = (
            f"{self.game.last_action} {self.game.last_card}\n"
            f"```md\n{self.game.player_list}```"
        )
        GAME_STATUS_EMBED.color = self.game.last_card.color_code
        GAME_STATUS_EMBED.set_thumbnail(url=self.game.last_card.image_url)
        GAME_STATUS_EMBED.set_footer(text=f"You have {floor(self.game.data.turn_time / 60)} minutes to play.")

        await self.thread.send(embed=GAME_STATUS_EMBED, view=view)


    async def create_new_menu(self, *buttons: Tuple[discord.ui.Button, ...]) -> PlayerTurnView:
        player_turn_menu = PlayerTurnView(timeout=self.game.data.turn_time, game=self.game)
        for button in buttons:
            player_turn_menu.add_item(button)
        return player_turn_menu

