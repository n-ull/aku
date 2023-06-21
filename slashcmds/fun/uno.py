import discord
from games.uno.game import Main
from discord import app_commands, Interaction

@app_commands.command()
async def uno(ctx: Interaction):
    """Juega UNO y pierde tus amigos."""
    await ctx.response.defer()
    main = Main(ctx=ctx)
    
    await main.start_main()

async def setup(bot):
    bot.tree.add_command(uno)