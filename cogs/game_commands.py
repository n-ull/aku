import discord
from discord.ext import commands
from game_base import GameBase

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

class GameCommands(commands.Cog):
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
    await bot.add_cog(GameCommands(bot))