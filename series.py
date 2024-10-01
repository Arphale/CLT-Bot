import discord
import discord.context_managers
from draft import draft
from datetime import datetime,timedelta


class series:
    def __init__(self,client:discord.client,user_1:discord.member,user_2:discord.member,list_of_valid:list,best_of_n:int=3) -> None:
        self.client = client
        self.best_of_n = best_of_n
        self.score_to_win = best_of_n//2+1
        self.date_start = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        self.user_1 = user_1
        self.user_2 = user_2
        self.user_1_score = 0
        self.user_2_score = 0
        self.drafts = []
        self.list_of_valid = list_of_valid
        self.list_of_bans = []
        self.waiting_on_confirmation = set()
        self.winner = None

    def __str__(self) -> str:
        
        string = f"{self.date_start}\nBest of Three Series between {self.user_1.mention} and {self.user_2.mention}\n"
        if (len(self.drafts))>0:
            for draft in self.drafts:
                string += str(draft) +"\n"
        else:
            string += "Waiting for game 1 draft"
        return string
    
    def accepted(self,user_1,user_2):
        if user_1 not in self.waiting_on_confirmation and user_2 not in self.waiting_on_confirmation:
            return True
        else:
            False

    async def run(self,ctx):
        while not (self.user_1_score>=self.score_to_win or self.user_2_score>=self.score_to_win):
            await self.ready_for_next_game(ctx=ctx)
            game = draft(client=self.client,blue_side_user=self.user_1,red_side_user=self.user_2,list_of_valid=self.list_of_valid,list_of_bans=self.list_of_bans,gameNb=len(self.drafts)+1)
            self.drafts.append(game)
            await ctx.send(f"**Beginning GAME {len(self.drafts)}**")
            await game.run(ctx=ctx)
            await self.updateScore(game)
            self.list_of_bans=game.list_of_banned
            continue
        if (self.user_1_score>=self.score_to_win or self.user_2_score>=self.score_to_win):
            await self.conclude_series(ctx=ctx)
    
    async def conclude_series(self,ctx):
        if self.user_1_score>=self.score_to_win:
            self.winner = self.user_1
        elif self.user_2_score>=self.score_to_win:
            self.winer = self.user_2
        else:
            raise Exception("Something went wrong, no winner was declared")
        await ctx.send(f"{str(self)}\n {self.winner.mention} WINS THE SERIES!")


    async def confirm_series(self,ctx,timeout:int=300)->bool:
        return await self.ask_confirmation(ctx,timeout,"starting series")

    async def ready_for_next_game(self,ctx,timeout:int=600)->bool:
        return await self.ask_confirmation(ctx,timeout,"waiting for next draft")

    async def ask_confirmation(self,ctx,time_limit,reason)->bool:
        self.waiting_on_confirmation.add(self.user_1)
        self.waiting_on_confirmation.add(self.user_2)
        
        future_time = datetime.now() + timedelta(seconds=time_limit)
        unix_timestamp = int(future_time.timestamp())
        if reason == "starting series":
            await ctx.send(f"Draft started between {self.user_1.mention} and {self.user_2.mention}!\nBoth users need to accept the draft using `!accept`. You have {time_limit} minutes. (<t:{unix_timestamp}:R>) ")
        elif reason== "waiting for next draft":
            await ctx.send(f"{self.user_1.mention} and {self.user_2.mention}, need users need to accept to start the next draft using `!accept`.")
        def check(msg):
            return(
                msg.author in self.waiting_on_confirmation
                and msg.channel == ctx.channel
                and msg.content.startswith("!accept")
            )

        while not self.accepted(self.user_1,self.user_2):
            try:
                msg = await self.client.wait_for("message",check=check,timeout=time_limit)
                self.waiting_on_confirmation.remove(msg.author)
            except TimeoutError:
                await ctx.send(f"The match was not accepted in time.")
                return
        return self.accepted(self.user_1,self.user_2)

    async def updateScore(self,game):
        if game.winner == self.user_1:
            self.user_1_score += 1
        elif game.winner == self.user_2:
            self.user_2_score += 1
        else:
            raise Exception("no winner was found")