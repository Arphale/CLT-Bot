import discord
import discord.context_managers
from draft import draft
import datetime

class series:
    def __init__(self,client:discord.client,user_1:discord.member,user_2:discord.member,list_of_valid:list,best_of_n:int=3) -> None:
        self.client = client
        self.best_of_n = best_of_n
        self.points_to_win = best_of_n//2
        self.date_start = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        self.user_1 = user_1
        self.user_2 = user_2
        self.blue_score = 0
        self.red_score = 0
        self.drafts = []
        self.list_of_valid = list_of_valid
        self.list_of_bans = []

    def __str__(self) -> str:
        
        string = f"{self.date_start}\nBest of Three Series between {self.user_1.mention} and {self.user_2.mention}\n"
        if (len(self.drafts))>0:
            for draft in self.drafts:
                string += draft +"\n"
        else:
            string += "Waiting for game 1 draft"
        return string

    async def run(self,ctx):
        while self.red_score<self.points_to_win and self.blue_score<self.points_to_win:
            game = draft(client=self.client,blue_side_user=self.user_1,red_side_user=self.user_2,list_of_valid=self.list_of_valid)
            await game.run(ctx=ctx)
            await self.updateScore(game)
            self.drafts.append(game)
            print(self)
        

    async def updateScore(self,game):
        if game.winner == self.user_1:
            self.blue_score += 1
        elif game.winner == self.user_2:
            self.red_score += 1
        else:
            raise Exception("no winner was found")