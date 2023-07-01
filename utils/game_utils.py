from enum import Enum
import discord
from game_base import GameConfig
import games.uno.game as UNO

class GameType(Enum):
    UNO = UNO.UNOGame

class GameManager:
    def __init__(self, bot) -> None:
        self.bot = bot
        self.games: dict = bot.games

    def get_guild_dictionary(self, guild_id: int, thread_id: int | None = None):
        guild: dict = self.games.get(guild_id, None)

        if guild is not None and thread_id is not None:
            game = guild.get(thread_id, None)
            return game
        else:
            return guild
    
    def check_game_instance(self, guild_dict: dict, game_type: GameType) -> bool:
        if guild_dict == None: return False
        for thread_id, game_instance in guild_dict.items():
            if isinstance(game_instance, game_type.value):
                return True
            else: return False

    def register(self, guild_id, thread_id, game):
        self.games[guild_id] = dict()
        self.games[guild_id][thread_id] = game
    
    async def start_game(self, ctx: discord.Interaction, game: GameType, configuration: GameConfig):
        # set the tread
        configuration.owner = ctx.user
        thread = await ctx.channel.create_thread(name=f"{game.name} > {ctx.guild.name}", reason=f"Game started by {configuration.owner.display_name}",type=discord.ChannelType.public_thread)
        configuration.thread = thread
        game_instance = game.value(data=configuration)
        self.register(guild_id=ctx.guild.id, thread_id=thread.id, game=game_instance)
        await game_instance.message_handler.start_message()
        return game_instance
        
    def unregister(self, guild_id, thread_id):
        del self.games[guild_id][thread_id]
        if len(self.games[guild_id]) == 0: del self.games[guild_id]
