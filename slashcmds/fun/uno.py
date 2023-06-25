import discord
from discord import app_commands

import settings
from games.uno.game import Main

logger = settings.logging.getLogger("game")


@app_commands.command()
@app_commands.describe(randomize="Randomize player list at start?")
@app_commands.choices(randomize=[app_commands.Choice(name="True", value=1), app_commands.Choice(name="False", value=0)])
@app_commands.guild_only()
async def uno(ctx: discord.Interaction, randomize: int = 0):
    """Lose all your friends."""
    try:
        if ctx.guild_id in ctx.client.games:
            return await ctx.response.send_message("Can't open another game in the same guild.")
        main = Main(ctx=ctx, randomize=randomize == 0)
        await main.start()
    except Exception as e:
        logger.exception(f"UNO: AN EXCEPTION OCCURRED: {e}")
    finally:
        # logger.info("UNO GAME ENDED! CLEANING...")
        result_embed: discord.Embed = discord.Embed(title=f"UNO! {ctx.user.display_name} finished:")
        if main.game.status.name != "FINISHED":
            result_embed.description = "Game has been cancelled."
            await ctx.channel.send(embed=result_embed)
        else:
            for player in main.game.players:
                await ctx.client.db.add_uno_game(player.id)

            await ctx.client.db.add_uno_win(main.game.winner.id)
            user_db = await ctx.client.db.uno_wins(main.game.winner.id)

            result_embed.description = (
                f"The winner is: {main.game.winner.name}\n"
                f"{main.game.winner.name} won a total of {user_db['wins']} games.\n"
                f"Win rate: {(user_db['wins'] / user_db['games']) * 100}%"
            )
            result_embed.color = main.game.graveyard.last_card.color_code
            result_embed.set_thumbnail(url=main.game.graveyard.last_card.image_url)
            await ctx.channel.send(embed=result_embed)
        del ctx.client.games[ctx.guild_id]


async def setup(bot):
    bot.tree.add_command(uno)
