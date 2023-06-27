import discord
from utils.game_utils import search_guild_game
from discord.ext import commands

class GameManager(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot : commands.Bot = bot

    # should listen when game thread is deleted
    # add win point (game)
    # add game counter (game)
    # add guild id and game to bot memory

    # command: leave
    # command: close
    # debug commands: win game
    # debug commands: del player

    # @commands.Cog.listener("on_interaction")
    # async def game_button(self, interaction: discord.Interaction):
    #     if interaction.type.value == 3:
    #             if interaction.data.get("custom_id") == "hand":
    #                  print("Hand pressed")


async def setup(bot):
    await bot.add_cog(GameManager(bot))