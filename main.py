import discord
from discord.ext import commands

import settings
from utils.database import AkuDatabase

logger = settings.logging.getLogger("bot")


def run():
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix="?", intents=intents, help_command=None)
    bot.games: dict = dict()
    bot.db = AkuDatabase(settings.MONGO_URI)

    # TODO: No funciona
    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error):
        if isinstance(error, commands.BotMissingPermissions):
            await interaction.response.send_message(content=error, ephemeral=True)
        else:
            raise error

    @bot.event
    async def on_ready():
        logger.info(f"User: {bot.user} (ID: {bot.user.id})")

        await bot.load_extension("cogs.debugger")
        await bot.change_presence(activity=discord.Game(name="Python Version"))

        for slashcmd_file in settings.SCMD_DIR.rglob("*.py"):
            group = slashcmd_file.parent.name
            if slashcmd_file.name != "__init__.py":
                await bot.load_extension(f"slashcmds.{group}.{slashcmd_file.name[:-3]}")

        for guild in settings.TEST_GUILDS:
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync()

    # @bot.event
    # async def on_thread_delete(thread: discord.Thread):
    #     if thread.guild.id in bot.games and thread.id == bot.games[thread.guild.id].game.thread.id:
    #         await bot.games[thread.guild.id].thread_deleted()

    bot.run(settings.DISCORD_API_TOKEN, root_logger=True)


if __name__ == "__main__":
    run()
