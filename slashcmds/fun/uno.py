import discord
import settings
from games.uno.game import GameManager
from discord import app_commands
logger = settings.logging.getLogger("game")

@app_commands.command()
@app_commands.guild_only()
@app_commands.describe(randomize="Randomize player list at start?")
@app_commands.choices(randomize=[
    app_commands.Choice(name="True", value=1),
    app_commands.Choice(name="False", value=0)
])
@app_commands.checks.bot_has_permissions(manage_threads=True, send_messages_in_threads=True)
async def uno(ctx: discord.Interaction, randomize: int = 0):
    """Lose all your friends."""
    try:
        await ctx.response.defer()
        game_manager = GameManager(ctx)
        start_menu = await game_manager.start_menu_func(ctx)
    except:
        print("An error occurred")
    finally:
        print("UNO command ended")
        # if start_menu.foo == None: print("Timedout")
        # if start_menu.foo == True: 
            # Comenzar el juego

async def setup(bot):
    bot.tree.add_command(uno)