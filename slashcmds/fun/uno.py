import discord
from games.uno.game import Main
from discord import app_commands

@app_commands.command()
@app_commands.guild_only()
async def uno(ctx: discord.Interaction):
    """Lose all your friends."""
    main = Main(ctx=ctx)
    await main.start()

async def setup(bot):
    bot.tree.add_command(uno)