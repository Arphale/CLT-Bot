import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import myCommands

# Load environment variables from .env file
load_dotenv()

# Set up intents
intents = discord.Intents.all()

# Create bot instance with command prefix and intents
client = commands.Bot(command_prefix="!", intents=intents)

# Replace 'YOUR_GUILD_ID' with the ID of the server you want to test in
GUILD_ID = os.getenv('GUILD_ID')  # Ensure you have this in your .env file

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    try:
        # Sync commands to a specific guild for faster visibility during testing
        guild = discord.Object(id=GUILD_ID)
        synced = await client.tree.sync(guild=guild)
        print(f"Synced {len(synced)} command(s) to guild {GUILD_ID}")
    except Exception as e:
        print(e)

# Define a slash command 'hello' for the specific guild
@client.tree.command(name="hello", guild=discord.Object(id=GUILD_ID))
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hey {interaction.user.mention}! This is a slash command!", ephemeral=True)

# Define a slash command 'say' for the specific guild
@client.tree.command(name="say", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(arg="What should I say?")
async def say(interaction: discord.Interaction, arg: str):
    await interaction.response.send_message(f"Hey {interaction.user.mention} said: '{arg}'")

@client.tree.command(name="ping", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="Who should I ping?")
async def ping(interaction: discord.Interaction, member: discord.User):
    await interaction.response.send_message(f"Hey {member.mention}!")

@client.tree.command(name="createevent", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(title="What is this event?",description="What is this event about?",date="what day is this event? Format: DD-MM-YYYY",time="when is this event? Format:  HH:MM (UTC)")
async def createEvent(interaction: discord.Interaction, title: str, description: str, date:str, time:str):
    await interaction.response.send_message(embed=myCommands.createEvent(title=title, description=description, date=date, time=time))
    return

# Define non-slash commands
@client.event
async def on_message(message:discord.Message):
    # Ensure the bot ignores its own messages
    if message.author == client.user:
        return

    if message.content.startswith("Quoi?"):
        await message.channel.send(myCommands.quoi())

    # Allows commands to be processed
    await client.process_commands(message)

# Run the bot with the token from the environment variable
client.run(os.getenv('TOKEN'))
