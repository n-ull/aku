from discord import Interaction, app_commands


@app_commands.command()
async def ping(ctx: Interaction):
    """Hace pong pong jeje je je..."""
    await ctx.response.send_message("pong!")


async def setup(bot):
    bot.tree.add_command(ping)
