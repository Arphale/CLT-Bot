import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from random import randint

def createEvent(title:str,description: str, date:str, time:str) -> discord.Embed:
    
    year=   int(date[6]+date[7]+date[8]+date[9]) 
    month=  int(date[3]+date[4])
    day=    int(date[0]+date[1])
    hour=   int(time[0]+time[1])
    minute= int(time[3]+time[4])
     
    
    timestamp=datetime(year=year,month=month,day=day,hour=hour,minute=minute)
    embed = discord.Embed(title=title,color=0x00ff00,description=description,timestamp=timestamp)
    return embed

def quoi():
    if randint(0,1)==0:
        return "Feur!"
    else:
        return "Coubeh!"