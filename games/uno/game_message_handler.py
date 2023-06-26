import discord
from game_base import GameBase
from typing import Tuple


class TurnOptionsView(discord.ui.View):
    def __init__(self, *, timeout: float | None = None, ephemeral_message: discord.WebhookMessage):
        super().__init__(timeout=timeout)
        self.ephemeral_message = ephemeral_message

    async def close_view(self):
        await self.ephemeral_message.edit(view=None)
        self.view.opened = False
        self.stop()

class HandButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        print("This is the hand button")
        # checks if hand has been opened before:
        if self.view.opened:
            # edit the last hand message
            await self.view.last_hand_msg.edit(content="Hand button pressed again")
            ...

        # remember the hand button:
        await interaction.response.defer()
        self.view.opened = True
        self.view.last_hand_msg = await interaction.followup.send(content="Test message")

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
        self.turn_options_view: TurnOptionsView | None = None # this is empty until the current player touches the hand button
        self.last_hand_msg : discord.WebhookMessage | None = None
        self.opened: bool = False # this will remember if the player used the button inside the view.

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
        # view: discord.ui.View | None = await self.create_new_menu(buttons)
        await self.thread.send((
            f"{self.game.last_action}"
        ), view=view)


    async def create_new_menu(self, *buttons: Tuple[discord.ui.Button, ...]) -> PlayerTurnView:
        player_turn_menu = PlayerTurnView(timeout=self.game.data.turn_time, game=self.game)
        for button in buttons:
            player_turn_menu.add_item(button)
        return player_turn_menu

