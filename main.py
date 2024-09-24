import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# Set up intents
intents = discord.Intents.default()
intents.message_content = True

# Create bot instance with command prefix and intents
client = commands.Bot(command_prefix="!", intents=intents)

# Draft data storage
ongoing_drafts = {}
picked_weapons = set()  # To keep track of picked weapons

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
    ongoing_drafts[blueSideUser.id] = {"picks": [], "turn": True, "pick_count": 1, "blueSide": True}
    ongoing_drafts[redSideUser.id] = {"picks": [], "turn": False, "pick_count": 1, "blueSide": False}
    
    await ctx.send(f"Draft started between {blueSideUser.mention} and {redSideUser.mention}!")
    
    # Start with blue side's pick
    await prompt_pick(ctx, blueSideUser, redSideUser)

async def prompt_pick(ctx, current_user, next_user):
    # Determine pick label
    pick_number = ongoing_drafts[current_user.id]["pick_count"]
    pick_label = f"B{pick_number}" if ongoing_drafts[current_user.id]["blueSide"] else f"R{pick_number}"
    
    # Notify the current user and set timer
    time_limit = 60
    future_time = datetime.now() + timedelta(seconds=time_limit)
    unix_timestamp = int(future_time.timestamp())
    
    # Get current status of the draft
    draft_status = await get_draft_status()

    await ctx.send(f"{current_user.mention}, pick {pick_label}. You have {time_limit} seconds. (in <t:{unix_timestamp}:R>)\n\nCurrent Draft Status:\n{draft_status}")

    while True:
        # Wait for the user's pick
        def check(msg):
            return msg.author == current_user and msg.channel == ctx.channel and msg.content.startswith("!pick ")

        try:
            msg = await client.wait_for("message", check=check, timeout=time_limit)
            weapon = msg.content[6:].strip().lower()  # Remove the "!pick " part

            # Check if the weapon is already picked
            if weapon in picked_weapons:
                await ctx.send(f"{current_user.mention}, the weapon '{weapon}' has already been picked! Please choose a different one.")
                # Continue to loop until a valid weapon is chosen
                continue

            # Valid weapon selected
            ongoing_drafts[current_user.id]["picks"].append(weapon)
            picked_weapons.add(weapon)  # Add weapon to the picked set
            ongoing_drafts[current_user.id]["pick_count"] += 1
            await ctx.send(f"{current_user.mention} picked {weapon}.")
            break  # Exit loop after a valid pick

        except asyncio.TimeoutError:
            await ctx.send(f"{current_user.mention} took too long! Draft ended.")
            cleanup_draft(ctx, current_user, next_user)
            return

    # Switch turns and continue the draft sequence
    await next_turn(ctx, current_user, next_user)

async def get_draft_status():
    draft_status = []
    for user_id, data in ongoing_drafts.items():
        picks = ", ".join(data["picks"]) if data["picks"] else "None"
        user = await client.fetch_user(user_id)
        username = user.mention
        draft_status.append(f"{username}: {picks}")
    return "\n".join(draft_status)


async def next_turn(ctx, current_user, next_user):
    # Toggle turn
    ongoing_drafts[current_user.id]["turn"] = False
    ongoing_drafts[next_user.id]["turn"] = True

    blue_user = current_user if ongoing_drafts[current_user.id]["blueSide"] else next_user
    red_user = next_user if blue_user == current_user else current_user

    # Get the total picks made so far
    blue_picks = len(ongoing_drafts[blue_user.id]["picks"])
    red_picks = len(ongoing_drafts[red_user.id]["picks"])

    # Draft logic based on number of picks
    if blue_picks == 1 and red_picks == 0:
        await prompt_pick(ctx, red_user, blue_user)  # R1
        await prompt_pick(ctx, red_user, blue_user)  # R2

    if blue_picks == 1 and red_picks == 2:
        await prompt_pick(ctx, blue_user, red_user)  # B2
        await prompt_pick(ctx, blue_user, red_user)  # B3

    if blue_picks == 3 and red_picks == 2:
        await prompt_pick(ctx, red_user, blue_user)  # R3
        await prompt_pick(ctx, red_user, blue_user)  # R4

    if blue_picks == 3 and red_picks == 4:
        await prompt_pick(ctx, blue_user, red_user)  # B4
        await prompt_pick(ctx, blue_user, red_user)  # B5

    if blue_picks == 5 and red_picks == 4:
        await prompt_pick(ctx, red_user, blue_user)  # R5

    # Check if the draft has finished
    if len(ongoing_drafts[current_user.id]["picks"]) + len(ongoing_drafts[next_user.id]["picks"]) == 10:
        await end_draft(ctx, current_user, next_user)

async def end_draft(ctx, user1, user2):
    picks_user1 = ", ".join(ongoing_drafts[user1.id]["picks"])
    picks_user2 = ", ".join(ongoing_drafts[user2.id]["picks"])

    await ctx.send(f"Draft complete! Here are the picks:\n{user1.mention}: {picks_user1}\n{user2.mention}: {picks_user2}")
    
    # Cleanup
    cleanup_draft(ctx, user1, user2)

def cleanup_draft(ctx, user1, user2):
    # Remove users from ongoing drafts
    ongoing_drafts.pop(user1.id, None)
    ongoing_drafts.pop(user2.id, None)

# Run the bot with the token from the environment variable
client.run(os.getenv('TOKEN'))
