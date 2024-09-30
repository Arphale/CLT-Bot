import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
from datetime import datetime, timedelta
import json
from series import series

# Load environment variables from .env file
load_dotenv()

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Create bot instance with command prefix and intents
client = commands.Bot(command_prefix="!", intents=intents)

# Draft data storage
ongoing_drafts = {}
picked_weapons = set()  # To keep track of picked weapons
draft_acceptances = {}  # To track user acceptance for drafts

# Global dictionary to store available weapons by weapon line
available_weapons_by_line = {}
valid_weapons = []


# Function to load the available weapons from the 'weapons' directory
def load_available_weapons():
    global valid_weapons
    global available_weapons_by_line
    weapons_folder = 'weapons'

    # Iterate over weapon line folders
    for weapon_line in os.listdir(weapons_folder):
        weapon_line_path = os.path.join(weapons_folder, weapon_line)

        # Ensure it's a directory
        if os.path.isdir(weapon_line_path):
            weapons = []
            # Iterate over the image files in the weapon line directory
            for file in os.listdir(weapon_line_path):
                if file.endswith('.png'):
                    weapon_name = os.path.splitext(file)[0]  # Remove '.png'
                    weapons.append(weapon_name)
                    valid_weapons.append(weapon_name.strip().lower())

            # Store the weapons under their weapon line
            available_weapons_by_line[weapon_line] = weapons

# Call this function once during bot startup or when loading weapons
load_available_weapons()


@client.command(name="bo3")
async def bo3(ctx,user_1:discord.Member,user_2:discord.Member):
    global valid_weapons
    best_of_three = series(client=client,user_1=user_1,user_2=user_2,list_of_valid=valid_weapons)
    await best_of_three.run(ctx=ctx)



# Run the bot
client.run(os.getenv("TOKEN"))