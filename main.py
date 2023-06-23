import settings
import discord
from discord.ext import commands
from discord import app_commands

logger = settings.logging.getLogger("bot")

def run():
    intents = discord.Intents.default() 
    intents.message_content = True

    bot = commands.Bot(command_prefix="?", intents=intents, help_command= None)

    @bot.event
    async def on_ready():
        logger.info(f"User: {bot.user} (ID: {bot.user.id})")
        await bot.change_presence(activity=discord.Game(name="Python Version"))

        for cmd_file in settings.CMDS_DIR.glob("*.py"):
            if cmd_file.name != "__init__.py":
                await bot.load_extension(f"cmds.{cmd_file.name[:-3]}")
        
        for slashcmd_file in settings.SCMD_DIR.rglob("*.py"):
            group = slashcmd_file.parent.name
            if slashcmd_file.name != "__init__.py":
                await bot.load_extension(f"slashcmds.{group}.{slashcmd_file.name[:-3]}")

        bot.tree.copy_global_to(guild=settings.TEST_GUILD_ID)
        await bot.tree.sync(guild=settings.TEST_GUILD_ID)


    bot.run(settings.DISCORD_API_TOKEN, root_logger=True)

if __name__ == "__main__":
    run()