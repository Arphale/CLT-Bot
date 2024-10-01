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
    global valid_weapons,ongoing_drafts,waiting_on_confirmation,client
    waiting_on_confirmation.add(user_1)
    waiting_on_confirmation.add(user_2)
    time_limit = 5
    future_time = datetime.now() + timedelta(minutes=time_limit)
    unix_timestamp = int(future_time.timestamp())
    await ctx.send(f"Draft started between {user_1.mention} and {user_2.mention}!\nBoth users need to accept the draft using `!accept`. You have {time_limit} minutes. (<t:{unix_timestamp}:R>) ")

    def check(msg):
        return(
            msg.author in waiting_on_confirmation
            and msg.channel == ctx.channel
            and msg.content.startswith("!accept")
        )

    while not accepted(user_1,user_2):
        try:
            msg = await client.wait_for("message",check=check,timeout=time_limit*60)
            waiting_on_confirmation.remove(msg.author)
        except TimeoutError:
            await ctx.send(f"The match was not accepted in time.")
            return

    best_of_three = series(client=client,user_1=user_1,user_2=user_2,list_of_valid=valid_weapons)
    ongoing_drafts.add(best_of_three)
    await best_of_three.run(ctx=ctx)


# Run the bot
client.run(os.getenv("TOKEN"))