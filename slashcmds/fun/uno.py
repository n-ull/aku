import discord
from discord import app_commands
import games.uno.game_config as UNO
import utils.game_utils as game_utils

boolean_options = [
    app_commands.Choice(name="True", value=1),
    app_commands.Choice(name="False", value=0)
]

time_options = [
    app_commands.Choice(name="1 minute", value=60),
    app_commands.Choice(name="2 minutes", value=120),
    app_commands.Choice(name="3 minutes", value=180),
]

@app_commands.command()
@app_commands.guild_only()
@app_commands.describe(randomize="Randomize player list at start?", stackable="Do you want to allow stack +2?",turn_time="How long is each turn?")
@app_commands.choices(randomize=boolean_options, stackable=boolean_options, turn_time=time_options)
@app_commands.checks.bot_has_permissions(manage_threads=True, send_messages_in_threads=True)
async def uno(ctx: discord.Interaction, randomize: int = 0, stackable: int= 1, turn_time: int = 180):
    """Lose all your friends."""
    if ctx.channel.type.name != "text": return await ctx.response.send_message("You can't use this command here!", ephemeral=True)
    GAME_MANAGER = game_utils.GameManager(ctx.client)
    GUILD_DICT = GAME_MANAGER.get_guild_dictionary(guild_id=ctx.guild_id)
    EXISTING_GAME = GAME_MANAGER.check_game_instance(guild_dict=GUILD_DICT,game_type=game_utils.GameType.UNO)

    if GUILD_DICT is not None:
        if GAME_MANAGER.check_game_instance(guild_dict=GUILD_DICT, game_type=game_utils.GameType.UNO):
            await ctx.response.send_message("Someone is already playing UNO in this guild.")
    elif not EXISTING_GAME or EXISTING_GAME == None:
        await ctx.response.defer()
        bool = [False, True]
        configuration = UNO.UnoGameConfig(client=ctx.client, stackable=bool[stackable], randomize_players=bool[randomize], turn_time=turn_time)
        game = await GAME_MANAGER.start_game(ctx=ctx, game=game_utils.GameType.UNO, configuration=configuration)
        await ctx.edit_original_response(content="Game Started...")
async def setup(bot):
    bot.tree.add_command(uno)