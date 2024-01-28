# environment variables
import os
from dotenv import load_dotenv

import discord
from discord.ext import commands

# web scraping
import cexStockChecker as csc

# time delays
import time
import asyncio


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

#should move this to JSON later as a config file
showDescription = True

#Discord bot
#client = discord.Client(intents=discord.Intents.default())
client = commands.Bot(intents=discord.Intents.default(), command_prefix='!')

@client.command()
async def checkStockChanges(ctx):
    channel = client.get_channel(CHANNEL_ID)
    listings = await csc.main()
    newListings = listings[0]
    soldListings = listings[1]

    if len(newListings) == 0: 
        embed = discord.Embed(
            title = "No new listings",
            color = discord.Color.orange()
        )
        await channel.send(embed=embed)
    else:
        for newIndex in range (0, len(newListings)):
            embed = discord.Embed(
                title = newListings[newIndex],
                color = discord.Color.red()
            )
            embed.add_field(name="Price", value = newListings[newIndex])
            await channel.send(embed=embed)

    if len(soldListings) == 0: 
            embed = discord.Embed(
                title = "No sold listings",
                color = discord.Color.orange()
            )
            await channel.send(embed=embed)
    else:
         for soldIndex in range (0, len(soldListings)):
            embed = discord.Embed(
                title = soldListings[soldIndex],
                color = discord.Color.red()
            )
            embed.add_field(name="Price", value = soldListings[soldIndex])
            await channel.send(embed=embed)
            
@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

# Run the Discord bot       
client.run(TOKEN)