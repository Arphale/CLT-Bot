import discord

from datetime import timedelta,datetime
import random
class draft:
    def __init__(self,client:discord.client,blue_side_user:discord.member,red_side_user:discord.member,list_of_bans:list=[],list_of_valid:list=[],gameNb:int=1) -> None:
        self.client = client
        self.blue_side_user = blue_side_user
        self.red_side_user = red_side_user
        self.list_of_valid = list_of_valid

        self.gameNb = gameNb
        self.list_blue_picks = []
        self.list_red_picks = []
        self.list_of_banned = list_of_bans
        self.winner = None

    def __str__(self) -> str:
        string = f"Game {self.gameNb}: {self.blue_side_user.mention} vs {self.red_side_user.mention} \n {self.get_draft_status()} \n"
        if self.winner is not None:
            string += f". winner: {self.winner.mention}" 
        return  (string)

    async def run(self,ctx):
        await self.promptPick(user=self.blue_side_user,ctx=ctx)
        await self.promptPick(user=self.red_side_user,ctx=ctx)
        await self.promptPick(user=self.red_side_user,ctx=ctx)
        await self.promptPick(user=self.blue_side_user,ctx=ctx)
        await self.promptPick(user=self.blue_side_user,ctx=ctx)
        await self.promptPick(user=self.red_side_user,ctx=ctx)
        await self.promptPick(user=self.red_side_user,ctx=ctx)
        await self.promptPick(user=self.blue_side_user,ctx=ctx)
        await self.promptPick(user=self.blue_side_user,ctx=ctx)
        await self.promptPick(user=self.red_side_user,ctx=ctx)
        await ctx.send(self.get_draft_status())
        await self.getWinner(ctx=ctx)

    def get_draft_status(self)->str:
        draft_status = []
        users = [self.blue_side_user,self.red_side_user]
        # Calculate the maximum length of the usernames for alignment
        max_mention_length = max(len(str(self.client.get_user(user.id))) for user in users)
        max_weapon_length = max(len(weapon) for weapon in self.list_blue_picks+self.list_red_picks or ["None"]) # Set a fixed length for weapon names


        # blue side formatting
        stripped_mention = str(self.client.get_user(self.blue_side_user.id)).ljust(max_mention_length)
        formatted_picks = [f"`{weapon.ljust(max_weapon_length)}`" for weapon in self.list_blue_picks or ["None"]]
        picks = ", ".join(formatted_picks)
        draft_status.append(f"`{stripped_mention}`: {picks}")

        # red side formatting
        stripped_mention = str(self.client.get_user(self.red_side_user.id)).ljust(max_mention_length)
        formatted_picks = [f"`{weapon.ljust(max_weapon_length)}`" for weapon in self.list_red_picks or ["None"]]
        picks = ", ".join(formatted_picks)
        draft_status.append(f"`{stripped_mention}`: {picks}")

        return "\n".join(draft_status)

    async def promptPick(self,user:discord.member,ctx):
        blue_side = user == self.blue_side_user
        if blue_side:
            pick_label = f"B{len(self.list_blue_picks)+1}"
        else:
            pick_label = f"R{len(self.list_red_picks)+1}"

        time_limit = 60
        future_time = datetime.now() + timedelta(seconds=time_limit)
        unix_timestamp = int(future_time.timestamp())
        draft_status = self.get_draft_status()
        await ctx.send(f"{user.mention}, pick {pick_label} using the `!pick WEAPON` command (replace WEAPON with your pick). You have {time_limit} seconds. (<t:{unix_timestamp}:R>)\n\nCurrent Draft Status:\n{draft_status}")
        while True:
            def check(msg):
                return msg.author == user and msg.channel == ctx.channel and msg.content.startswith("!pick ")

            try:
                msg = await self.client.wait_for("message", check=check, timeout=time_limit)
                weapon = msg.content[6:].strip().lower()  # Remove the "!pick " part
                if weapon !="random":
                    if weapon not in self.list_of_valid:
                        await ctx.send(f"{user.mention}, '{weapon}' is not a valid weapon! Please choose a valid weapon from the list.")
                        continue
                    if weapon in self.list_of_banned:
                        await ctx.send(f"{user.mention}, the weapon '{weapon}' has already been picked! Please choose a different one.")
                        continue
                else:
                    weapon =  self.list_of_valid[random.randint(0,len(self.list_of_valid)-1)]
                    await ctx.send(f"{user.mention} has selected a random weapon, he gets {weapon}.")

                if blue_side:
                    self.list_blue_picks.append(weapon)
                else:
                    self.list_red_picks.append(weapon)
                self.list_of_banned.append(weapon)
                await ctx.send(f"{user.mention} picked {weapon}.")
                break  # Exit loop after a valid pick
                 

            except TimeoutError:
                await ctx.send(f"{user.mention} took too long! picking random weapon.")
                weapon = self.list_of_valid[random.randint(0,len(self.list_of_valid)-1)]
                if blue_side:
                    self.list_blue_picks.append(weapon)
                else:
                    self.list_red_picks.append(weapon)
                self.list_of_banned.append(weapon)
                await ctx.send(f"{user.mention} picked {weapon}.")
                return

    async def getWinner(self, ctx):
        time_limit = 35  # Set the time limit
        future_time = datetime.now() + timedelta(minutes=time_limit)
        unix_timestamp = int(future_time.timestamp())
        
        blue_side_user_confirmed = None
        red_side_user_confirmed = None
        
        await ctx.send(f"{self.blue_side_user.mention}, {self.red_side_user.mention}, pick the winner using the `!winner @user` command (replace @user with a mention of the winner). Both users need to type the command to confirm the result. You have {time_limit} minutes. (<t:{unix_timestamp}:R>)")

        while not (blue_side_user_confirmed and red_side_user_confirmed):
            def check(msg):
                return (
                    msg.author in [self.blue_side_user, self.red_side_user] 
                    and msg.channel == ctx.channel 
                    and msg.content.startswith("!winner ")
                )

            try:
                msg = await self.client.wait_for("message", check=check, timeout=time_limit * 60)
                mentioned_user = msg.mentions[0] if msg.mentions else None
                
                if mentioned_user not in [self.blue_side_user, self.red_side_user]:
                    await ctx.send(f"{msg.author.mention}, you need to mention either {self.blue_side_user.mention} or {self.red_side_user.mention} as the winner!")
                    continue

                if msg.author == self.blue_side_user:
                    blue_side_user_confirmed = mentioned_user
                    await ctx.send(f"{self.blue_side_user.mention} declared {mentioned_user.mention} as the winner.")
                else:
                    red_side_user_confirmed = mentioned_user
                    await ctx.send(f"{self.red_side_user.mention} declared {mentioned_user.mention} as the winner.")

                # Check if both users declared the same winner
                if blue_side_user_confirmed and red_side_user_confirmed:
                    if blue_side_user_confirmed == red_side_user_confirmed:
                        self.winner = blue_side_user_confirmed
                        await ctx.send(f"Winner confirmed: {self.winner.mention}!")
                        return
                    else:
                        # Reset the confirmations if they don't match
                        blue_side_user_confirmed = None
                        red_side_user_confirmed = None
                        await ctx.send(f"The declarations do not match! Please try again.")
                        
            except TimeoutError:
                await ctx.send(f"Time's up! No winner was declared in time.")
                return
