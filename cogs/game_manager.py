import discord
from discord.ext import commands
from game_base import GameBase, GameConfig

"""
game store dict:
guild_id: list[dict] = {
    thread_id: {
        game
    },
    thread_id: {
        game
    }
}
"""

class GameManager(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot : commands.Bot = bot
        self.games: dict = bot.games

    def check_existing_game(self, guild_id: int, thread_id: int | None = None):
        guild: dict = self.games.get(guild_id, None)

        if guild is not None and thread_id is not None:
            game = guild.get(thread_id, None)
            return game
        else:
            return guild
        
    def register(self, guild_id, thread_id, game):
        self.games[guild_id] = dict()
        self.games[guild_id][thread_id] = game
    
    async def start_game(self, ctx: discord.Interaction, game: GameBase, configuration: GameConfig):
        # set the tread
        thread = await ctx.channel.create_thread(name=game, message=f"{game}", reason=f"Game started by {configuration.owner.display_name}")
        configuration.thread = thread
        self.register(guild_id=ctx.guild_id, thread_id=thread.id, game=game(configuration))
        game.message_handler.start_message()
        
    def unregister(self, guild_id, thread_id):
        del self.games[guild_id][thread_id]

    
    @commands.command(name="leave")
    async def leave_game(self, ctx: commands.Context):
        if ctx.channel.type.name == "public_thread":
            game: GameBase = self.check_existing_game(ctx.guild.id, ctx.channel.id)
            if game is not None:
                player = game.get_player_by_id(ctx.author.id)
                if player is not None: 
                    await game.del_player(player)
                    if len(game.players) >= 2: await ctx.send(f"{ctx.author.display_name} left the game.")
            # await ctx.send("Leaving game") if a is not None else await ctx.send("There's no game in this thread")
        
    @commands.command(name="register")
    async def register_game(self, ctx: commands.Context, *args: str):
        """Registra un juego copiando thread y guild"""
        game = self.check_existing_game(guild_id=ctx.guild.id, thread_id=ctx.channel.id)

        if ctx.channel.type.name == "public_thread" and game is None:
            self.register(guild_id=ctx.guild.id, thread_id=ctx.channel.id, game=args)
            await ctx.send(f"Game registered: {args}...")

    @commands.command(name="delete")
    async def unregister_game(self, ctx: commands.Context):
        """Borra un juego existente marcando guild y thread id"""
        if ctx.channel.type.name == "public_thread":
            self.unregister(guild_id=ctx.guild.id, thread_id=ctx.channel.id)
            await ctx.send("Game deleted...")

    @commands.command(name="existing")
    async def existing(self, ctx: commands.Context):
        """Muestra los juegos existentes en un mensaje"""
        guild = self.check_existing_game(ctx.guild.id)
        all_games = ""
        if guild is not None: 
            for game in guild:
                all_games += f"<#{game}> "
        await ctx.send(all_games) if guild else await ctx.send("Non existing games here!")


async def setup(bot):
    await bot.add_cog(GameManager(bot))