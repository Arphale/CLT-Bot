import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from series import series
from datetime import datetime,timedelta
# Load environment variables from .env file
load_dotenv()

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Create bot instance with command prefix and intents
client = commands.Bot(command_prefix="!", intents=intents)

# Draft data storage
ongoing_drafts = set()
waiting_on_confirmation = set()

# Global dictionary to store available weapons by weapon line
valid_weapons_by_line = {}
valid_weapons = []


# Function to load the available weapons from the 'weapons' directory
def load_available_weapons():
    global valid_weapons
    global valid_weapons_by_line
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
            valid_weapons_by_line[weapon_line] = weapons

# Call this function once during bot startup or when loading weapons
load_available_weapons()

def accepted(user_1,user_2):
    global waiting_on_confirmation
    if user_1 not in waiting_on_confirmation and user_2 not in waiting_on_confirmation:
        return True
    else:
        False

@client.command(name="bo3")
async def bo3(ctx,user_1:discord.Member,user_2:discord.Member):
    best_of_three = series(client=client,user_1=user_1,user_2=user_2,list_of_valid=valid_weapons)
    if best_of_three.confirm_series(ctx=ctx):
        ongoing_drafts.add(best_of_three)
        await best_of_three.run(ctx=ctx)

def find_current_draft(user:discord.user):
    for draft in ongoing_drafts:
        if user == draft.user_1 or user == draft.user_2:
            return draft
    return -1

@client.command(name="banned")
async def list_banned(ctx):
    draft = find_current_draft(ctx.author)
    if draft == -1:
        await ctx.send("You are not currently part of any draft.")
        return
    
    # Format banned weapons
    max_weapon_length=max(len(weapon) for weapon in draft.list_of_bans or ["None"])
    formatted_banned = [f"`{weapon.ljust(max_weapon_length)}`" for weapon in draft.list_of_bans] or ["`None`"]
    
    await ctx.send(f"**Banned Weapons:**\n{', '.join(formatted_banned)}")

# Command to list available weapons by weapon line
@client.command(name="available")
async def list_available(ctx):
    global valid_weapons_by_line
    draft = find_current_draft(ctx.author)
    if draft == -1:
        await ctx.send("You are not currently part of any draft.")
        return
    response = "**Available Weapons by Weapon Line:**\n"
    maxWeaponLength = 18
    # Format the weapons per weapon line
    for weapon_line, weapons in valid_weapons_by_line.items():
        availableWeapons=[]
        for weapon in weapons:
            if weapon.strip().lower() not in draft.list_of_bans:
                availableWeapons.append(f"`{weapon.ljust(maxWeaponLength)}`") 
        
        formatted_weapons = ', '.join(availableWeapons)
        response += f"\n**`{weapon_line.capitalize().ljust(12)}:`** {formatted_weapons}"

    # Split the message if it exceeds Discord's character limit
    if len(response) > 2000:
        lines = response.split("\n")
        firstMsg = ""
        secondMsg = ""
        index = 0
        while index < len(lines) and len(firstMsg)+len(lines[index])<2000:
            firstMsg += lines[index] + "\n"
            index+=1
        while index < len(lines):
            secondMsg += lines[index]+ "\n"
            index+=1

        await ctx.send(firstMsg)
        await ctx.send(secondMsg)
    else:
        await ctx.send(response)


# Run the bot
client.run(os.getenv("TOKEN"))