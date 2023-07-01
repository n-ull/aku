import discord
from discord.ext import commands
import games.uno.card as UNO

def is_bot_owner():
    async def predicate(ctx):
        return ctx.author.id == 244535132097216512
    return commands.check(predicate)

class Debugger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_bot_owner()
    async def card_add(self, ctx: commands.Context, *card):
        if ctx.guild.id in ctx.bot.games:
            game = ctx.bot.games[ctx.guild.id]
            player = game.get_player_by_id(ctx.author.id)
            player.hand.add_card(UNO.UnoCard(card[0], card[1]))
        else:
            await ctx.send(f"{card[0]} {card[1]}")

async def setup(bot):
    await bot.add_cog(Debugger(bot))