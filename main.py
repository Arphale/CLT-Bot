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

# Command to start the draft
@client.command(name="draft")
async def draft(ctx, user1: discord.Member, user2: discord.Member):
    # Ensure no other draft is ongoing for these users
    if ctx.author.id in ongoing_drafts or user1.id in ongoing_drafts or user2.id in ongoing_drafts:
        await ctx.send("A draft is already in progress with one of these users.")
        return
    
    # Initialize draft state
    ongoing_drafts[user1.id] = {"picks": [], "turn": True}
    ongoing_drafts[user2.id] = {"picks": [], "turn": False}
    
    await ctx.send(f"Draft started between {user1.mention} and {user2.mention}!")
    
    # Start with user1's pick
    await prompt_pick(ctx, user1, user2)

async def prompt_pick(ctx, current_user, next_user):
    # Calculate the timestamp for the end of the user's turn
    future_time = datetime.now() + timedelta(seconds=60)
    unix_timestamp = int(future_time.timestamp())

    await ctx.send(f"{current_user.mention}, it's your turn to pick a weapon! You have 60 seconds (until <t:{unix_timestamp}:R>).")
    
    def check(msg):
        return msg.author == current_user and msg.channel == ctx.channel and msg.content.startswith("!pick")

    try:
        msg = await client.wait_for("message", check=check, timeout=60.0)
        weapon = msg.content[6:].strip()  # Remove the "!pick " part
        ongoing_drafts[current_user.id]["picks"].append(weapon)
        await ctx.send(f"{current_user.mention} picked {weapon}.")
    except asyncio.TimeoutError:
        await ctx.send(f"{current_user.mention} took too long! Draft ended.")
        cleanup_draft(ctx, current_user, next_user)
        return

    # Switch turns and continue the draft sequence
    await next_turn(ctx, current_user, next_user)

async def next_turn(ctx, current_user, next_user):
    # Toggle turn
    ongoing_drafts[current_user.id]["turn"] = False
    ongoing_drafts[next_user.id]["turn"] = True

    # Get the number of picks made by each user
    user1_picks = len(ongoing_drafts[current_user.id]["picks"])
    user2_picks = len(ongoing_drafts[next_user.id]["picks"])

    # Check the number of picks to determine the next steps
    if user1_picks < 1:  # User1 picks first
        await prompt_pick(ctx, next_user, current_user)
    elif user1_picks < 3:  # User2 picks twice
        await prompt_pick(ctx, next_user, current_user)
        await prompt_pick(ctx, next_user, current_user)
    elif user2_picks < 3:  # User1 picks twice
        await prompt_pick(ctx, current_user, next_user)
        await prompt_pick(ctx, current_user, next_user)
    elif user2_picks < 5:  # User2 picks twice
        await prompt_pick(ctx, next_user, current_user)
        await prompt_pick(ctx, next_user, current_user)
    elif user1_picks < 6:  # User1 picks twice
        await prompt_pick(ctx, current_user, next_user)
        await prompt_pick(ctx, current_user, next_user)
    else:  # User2 picks once
        await prompt_pick(ctx, next_user, current_user)

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

# Command for users to pick a weapon
@client.command(name="pick")
async def pick(ctx, *, weapon: str):
    if ctx.author.id not in ongoing_drafts:
        await ctx.send("You're not in an ongoing draft!")
        return

    ongoing_drafts[ctx.author.id]["picks"].append(weapon)
    await ctx.send(f"{ctx.author.mention} picked {weapon}.")

# Run the bot with the token from the environment variable
client.run(os.getenv('TOKEN'))
