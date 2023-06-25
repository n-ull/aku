from discord import Interaction, app_commands

from games.blackjack.game import Blackjack, GameView


@app_commands.command()
async def blackjack(ctx: Interaction):
    """Juega Blackjack y pierde todas tus esperanzas de seguir vivo."""
    try:
        await ctx.response.defer()

        game_view = GameView()
        game = Blackjack(player_id=ctx.user.id, player=ctx.user)

        game_message = await ctx.followup.send(embed=game.game_embed(), view=game_view, wait=True)

        game_view.message = game_message
        game_view.game = game

        await game_view.wait()
    except:
        print("Blackjack Error")
    finally:
        print("Blackjack finished")


async def setup(bot):
    bot.tree.add_command(blackjack)
