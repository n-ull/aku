import discord
from discord import Embed, Interaction, app_commands

from utils.image_utils import calculate_image_hash_from_url
from utils.progress_bar import ProgressBar


@app_commands.command()
@app_commands.guild_only()
@app_commands.describe(user="Tu nobio")
async def gay(ctx: Interaction, user: discord.Member | None):
    """Revisa que tan gay eres tú o tu novio."""
    if user is None:
        user = ctx.user

    progress_bar = ProgressBar(length=14, filled_emoji="🏳️‍🌈")
    gay_level: int = calculate_image_hash_from_url(user.avatar) % 100

    embed = Embed()
    embed.set_author(name=f"Gay-o-meter - {user.display_name}", icon_url=user.avatar)
    embed.add_field(
        name=f"El nivel de homosexualidad de {user.display_name}:", value=progress_bar.show_progress(gay_level)
    )

    if gay_level == 0:
        embed.set_image(url="https://i.pinimg.com/originals/7f/2e/19/7f2e190365fde21a51610bf8c905fc9c.jpg")

    await ctx.response.send_message(embed=embed)


async def setup(bot):
    bot.tree.add_command(gay)
