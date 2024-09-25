import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
from datetime import datetime, timedelta
import json

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

# Command to set a timer
@client.command(name="timer")
async def timer(ctx, time: int):
    future_time = datetime.now() + timedelta(seconds=time)
    unix_timestamp = int(future_time.timestamp())
    await ctx.send(f"Timer set for {time} seconds: <t:{unix_timestamp}:R>")

# Command to start the draft
@client.command(name="draft")
async def draft(ctx, blueSideUser: discord.Member, redSideUser: discord.Member):
    # Ensure no other draft is ongoing for these users
    if blueSideUser.id in ongoing_drafts or redSideUser.id in ongoing_drafts:
        await ctx.send("A draft is already in progress with one of these users.")
        return

    # Initialize draft state
    ongoing_drafts[blueSideUser.id] = {"picks": [], "pick_count": 1, "blueSide": True, "user_id": blueSideUser.id}
    ongoing_drafts[redSideUser.id] = {"picks": [], "pick_count": 1, "blueSide": False, "user_id": redSideUser.id}

    # Initialize acceptance
    draft_acceptances[blueSideUser.id] = False
    draft_acceptances[redSideUser.id] = False

    await ctx.send(f"Draft started between {blueSideUser.mention} and {redSideUser.mention}!\n"
                   f"Both users need to accept the draft using `!accept draft`.")

# Command for users to accept the draft
@client.command(name="accept")
async def accept_draft(ctx, action: str):
    if action.lower() == "draft":
        # Check if the author is part of the draft
        if ctx.author.id in draft_acceptances:
            draft_acceptances[ctx.author.id] = True
            await ctx.send(f"{ctx.author.mention} has accepted the draft!")

            # Check if both users have accepted the draft
            if all(draft_acceptances.values()):
                await ctx.send("Both players have accepted! Starting the draft...")

                # Retrieve both user IDs from ongoing_drafts
                draft_data = list(ongoing_drafts.values())  # Get both users' draft data

                blue_side_user_data, red_side_user_data = None, None

                if draft_data[0]["blueSide"]:
                    blue_side_user_data = draft_data[0]
                    red_side_user_data = draft_data[1]
                else:
                    blue_side_user_data = draft_data[1]
                    red_side_user_data = draft_data[0]

                blue_user_id = blue_side_user_data["user_id"]
                red_user_id = red_side_user_data["user_id"]

                # Retrieve actual discord.Member objects from user IDs
                blue_side_user = ctx.guild.get_member(blue_user_id)
                red_side_user = ctx.guild.get_member(red_user_id)

                # Ensure both users exist
                if blue_side_user is None or red_side_user is None:
                    await ctx.send("One of the users is not found in the guild. Please check their presence.")
                    return

                # Proceed to the draft pick phase
                await prompt_pick(ctx, blue_side_user, red_side_user)
        else:
            await ctx.send("You are not part of an ongoing draft.")
    else:
        await ctx.send("Invalid action. Please use `!accept draft`.")

async def get_draft_status():
    draft_status = []
    
    # Calculate the maximum length of the usernames for alignment
    max_mention_length = max(len(str(client.get_user(user_id))) for user_id in ongoing_drafts)
    max_weapon_length = 20  # Set a fixed length for weapon names

    for user_id, data in ongoing_drafts.items():
        # Format weapon names with fixed length using .ljust()
        formatted_picks = [f"`{weapon.ljust(max_weapon_length)}`" for weapon in data["picks"]] or ["`None`"]
        picks = ", ".join(formatted_picks)

        # Adjust the length of the stripped mention (username without discriminator)
        stripped_mention = str(client.get_user(user_id)).ljust(max_mention_length)
        draft_status.append(f"`{stripped_mention}`: {picks}")
    return "\n".join(draft_status)

async def prompt_pick(ctx, picking_user, other_user):
    global valid_weapons

    # Determine pick label
    pick_number = ongoing_drafts[picking_user.id]["pick_count"]
    pick_label = f"B{pick_number}" if ongoing_drafts[picking_user.id]["blueSide"] else f"R{pick_number}"

    # Notify the current user and set timer
    time_limit = 60
    future_time = datetime.now() + timedelta(seconds=time_limit)
    unix_timestamp = int(future_time.timestamp())

    # Get current status of the draft
    draft_status = await get_draft_status()

    await ctx.send(f"{picking_user.mention}, pick {pick_label} using the `!pick WEAPON` command (replace WEAPON with your pick). You have {time_limit} seconds. (in <t:{unix_timestamp}:R>)\n\nCurrent Draft Status:\n{draft_status}")

    while True:
        # Wait for the user's pick
        def check(msg):
            return msg.author == picking_user and msg.channel == ctx.channel and msg.content.startswith("!pick ")

        try:
            msg = await client.wait_for("message", check=check, timeout=time_limit)
            weapon = msg.content[6:].strip().lower()  # Remove the "!pick " part
            
            # Check if the weapon is in the valid weapons list
            if weapon not in valid_weapons:
                await ctx.send(f"{picking_user.mention}, '{weapon}' is not a valid weapon! Please choose a valid weapon from the list.")
                # Continue to loop until a valid weapon is chosen
                continue

            # Check if the weapon is already picked
            if weapon in picked_weapons:
                await ctx.send(f"{picking_user.mention}, the weapon '{weapon}' has already been picked! Please choose a different one.")
                # Continue to loop until a valid weapon is chosen
                continue

            # Valid weapon selected
            ongoing_drafts[picking_user.id]["picks"].append(weapon)
            picked_weapons.add(weapon)  # Add weapon to the picked set
            ongoing_drafts[picking_user.id]["pick_count"] += 1
            await ctx.send(f"{picking_user.mention} picked {weapon}.")
            break  # Exit loop after a valid pick

        except asyncio.TimeoutError:
            await ctx.send(f"{picking_user.mention} took too long! Draft ended.")
            cleanup_draft(ctx, picking_user, other_user)
            return

    # Switch turns and continue the draft sequence
    await next_turn(ctx, picking_user, other_user)

async def next_turn(ctx, previous_picking_user, other_user):
    # Get the total picks made so far
    blue_side_user = previous_picking_user if ongoing_drafts[previous_picking_user.id]["blueSide"] == True else other_user
    red_side_user = other_user if blue_side_user == previous_picking_user else previous_picking_user

    blue_picks = len(ongoing_drafts[blue_side_user.id]["picks"])
    red_picks = len(ongoing_drafts[red_side_user.id]["picks"])

    # Draft logic based on number of picks
    if blue_picks == 0 and red_picks == 0:
        await prompt_pick(ctx, blue_side_user, red_side_user)  # B1
    if blue_picks == 1 and red_picks == 0:
        await prompt_pick(ctx, red_side_user, blue_side_user)  # R1
    if blue_picks == 1 and red_picks == 1:
        await prompt_pick(ctx, red_side_user, blue_side_user)  # R2
    elif blue_picks == 1 and red_picks == 2:
        await prompt_pick(ctx, blue_side_user, red_side_user)  # B2
    elif blue_picks == 2 and red_picks == 2:
        await prompt_pick(ctx, blue_side_user, red_side_user)  # B3
    elif blue_picks == 3 and red_picks == 2:
        await prompt_pick(ctx, red_side_user, blue_side_user)  # R3
    elif blue_picks == 3 and red_picks == 3:
        await prompt_pick(ctx, red_side_user, blue_side_user)  # R4
    elif blue_picks == 3 and red_picks == 4:
        await prompt_pick(ctx, blue_side_user, red_side_user)  # B4
    elif blue_picks == 4 and red_picks == 4:
        await prompt_pick(ctx, blue_side_user, red_side_user)  # B5
    elif blue_picks == 5 and red_picks == 4:
        await prompt_pick(ctx, red_side_user, blue_side_user)  # R5
    elif blue_picks == 5 and red_picks == 5:
        await end_draft(ctx=ctx, user1=blue_side_user,user2=red_side_user)

async def end_draft(ctx, user1, user2):
    status = await get_draft_status()
    await ctx.send(status)
    store_draft(ctx,user1,user2)
    # Cleanup
    cleanup_draft(ctx, user1, user2)

def store_draft(ctx,user1,user2):
    
    blue_side_user = user1 if ongoing_drafts[user1.id]["blueSide"] == True else user2
    red_side_user = user2 if blue_side_user == user1 else user1
    now = datetime.now()
    draft={}
    fileName = f"drafts\\{blue_side_user.name}_vs_{red_side_user.name}_{now.strftime('%m_%d_%Y_%H-%M-%S.json')}"
    
    with open(file=fileName,mode="w+") as file:
        draft["blue_user"]=blue_side_user.name
        draft["red_user"]=red_side_user.name
        draft["date and time"]=now.strftime('%m/%d/%Y %H:%M:%S')
        draft["b1"]=ongoing_drafts[blue_side_user.id]["picks"][0]
        draft["b2"]=ongoing_drafts[blue_side_user.id]["picks"][1]
        draft["b3"]=ongoing_drafts[blue_side_user.id]["picks"][2]
        draft["b4"]=ongoing_drafts[blue_side_user.id]["picks"][3]
        draft["b5"]=ongoing_drafts[blue_side_user.id]["picks"][4]
        draft["r1"]=ongoing_drafts[red_side_user.id]["picks"][0]
        draft["r2"]=ongoing_drafts[red_side_user.id]["picks"][1]
        draft["r3"]=ongoing_drafts[red_side_user.id]["picks"][2]
        draft["r4"]=ongoing_drafts[red_side_user.id]["picks"][3]
        draft["r5"]=ongoing_drafts[red_side_user.id]["picks"][4]
        json.dump(draft,file)

def cleanup_draft(ctx, blue_side_user, red_side_user):
    global picked_weapons

    # Cleanup logic here
    del ongoing_drafts[blue_side_user.id]
    del ongoing_drafts[red_side_user.id]
    draft_acceptances.pop(blue_side_user.id, None)
    draft_acceptances.pop(red_side_user.id, None)
    picked_weapons = set() 

@client.command(name="banned")
async def list_banned(ctx):
    if ctx.author.id not in ongoing_drafts:
        await ctx.send("You are not currently part of any draft.")
        return
    
    banned_weapons = [weapon for weapon in picked_weapons]
    
    # Format banned weapons
    max_weapon_length = 20  # Ensuring consistent length
    formatted_banned = [f"`{weapon.ljust(max_weapon_length)}`" for weapon in banned_weapons] or ["`None`"]
    
    await ctx.send(f"**Banned Weapons:**\n{', '.join(formatted_banned)}")

# Command to list available weapons by weapon line
@client.command(name="available")
async def list_available(ctx):
    response = "**Available Weapons by Weapon Line:**\n"
    maxWeaponLength = 18
    # Format the weapons per weapon line
    for weapon_line, weapons in available_weapons_by_line.items():
        availableWeapons=[]
        for weapon in weapons:
            if weapon.strip().lower() not in picked_weapons:
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