import discord
from discord.ext import commands
import asyncio
import config

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot online as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    

async def main():
    await bot.load_extension("cogs.tournament")
    await bot.load_extension("cogs.matches")
    await bot.load_extension("cogs.admin")
    await bot.start(config.DISCORD_TOKEN)

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"❌ Error: `{error}`")
    raise error

asyncio.run(main())