from __future__ import annotations 
from discord .ext import commands 
import discord 
import aiohttp 
import json 
import jishaku 
import asyncio 
import typing 
from typing import List 
import aiosqlite 
from utils .config import OWNER_IDS 
from utils import getConfig ,updateConfig 
from .Context import Context 
from discord .ext import commands ,tasks 
from colorama import Fore ,Style ,init 
import importlib 
import inspect 
from utils .Tools import get_ignore_data 
import random 

init (autoreset =True )

extensions :List [str ]=[
"cogs"
]

class Strelizia (commands .AutoShardedBot ):

    def __init__ (self ,*arg ,**kwargs ):
        intents =discord .Intents .all ()
        intents .presences =True 
        intents .members =True 
        super ().__init__ (command_prefix =self .get_prefix ,
        case_insensitive =True ,
        intents =intents ,
        status =discord .Status .idle ,
        strip_after_prefix =True ,
        owner_ids =OWNER_IDS ,
        allowed_mentions =discord .AllowedMentions (
        everyone =False ,replied_user =False ,roles =False ),
        sync_commands_debug =True ,
        sync_commands =True ,
        shard_count =2 )


        self .status_messages =[
        {"type":discord .ActivityType .watching ,"name":"over Strelizia HQ"},
        {"type":discord .ActivityType .listening ,"name":"to your commands"},
        {"type":discord .ActivityType .playing ,"name":"with Discord API"},
        {"type":discord .ActivityType .streaming ,"name":"&help | AeroX Development","url":"https://twitch.tv/strelizia"},
        {"type":discord .ActivityType .watching ,"name":"the Strelizia community"},
        {"type":discord .ActivityType .playing ,"name":"in Strelizia's digital garden"},
        {"type":discord .ActivityType .listening ,"name":"to Strelizia's heartbeat"},
        {"type":discord .ActivityType .watching ,"name":"for new Strelizia members"},
        {"type":discord .ActivityType .playing ,"name":"the role of your assistant"},
        {"type":discord .ActivityType .listening ,"name":"to feedback from Strelizia HQ"},
        {"type":discord .ActivityType .watching ,"name":"Strelizia bloom in cyberspace"},
        {"type":discord .ActivityType .playing ,"name":"guardian of Strelizia servers"}
        ]
        self .current_status_index =0 

    async def setup_hook (self ):
        await self .load_extensions ()
        self .status_rotation .start ()

    async def load_extensions (self ):
        for extension in extensions :
            try :
                await self .load_extension (extension )
            except Exception as e :
                print (
                f"{Fore.RED}{Style.BRIGHT}Failed to load extension {extension}. {e}"
                )


    async def on_connect (self ):
        await self .set_random_status ()

    @tasks .loop (seconds =10 )
    async def status_rotation (self ):
        await self .set_random_status ()

    async def set_random_status (self ):
        status_config =random .choice (self .status_messages )

        if status_config ["type"]==discord .ActivityType .streaming :
            activity =discord .Streaming (
            name =status_config ["name"],
            url =status_config .get ("url","https://twitch.tv/strelizia")
            )
        else :
            activity =discord .Activity (
            type =status_config ["type"],
            name =status_config ["name"]
            )

        await self .change_presence (status =discord .Status .idle ,activity =activity )

    @status_rotation .before_loop 
    async def before_status_rotation (self ):
        await self .wait_until_ready ()

    async def send_raw (self ,channel_id :int ,content :str ,
    **kwargs )->typing .Optional [discord .Message ]:
        await self .http .send_message (channel_id ,content ,**kwargs )

    async def invoke_help_command (self ,ctx :Context )->None :
        """Invoke the help command or default help command if help extensions is not loaded."""
        return await ctx .send_help (ctx .command )

    async def fetch_message_by_channel (
    self ,channel :discord .TextChannel ,
    messageID :int )->typing .Optional [discord .Message ]:
        async for msg in channel .history (
        limit =1 ,
        before =discord .Object (messageID +1 ),
        after =discord .Object (messageID -1 ),
        ):
            return msg 

    async def get_prefix (self ,message :discord .Message ):
        if message .guild :
            guild_id =message .guild .id 
            async with aiosqlite .connect ('db/np.db')as db :
                async with db .execute ("SELECT id FROM np WHERE id = ?",(message .author .id ,))as cursor :
                    row =await cursor .fetchone ()
                    if row :
                        data =await getConfig (guild_id )
                        prefix =data ["prefix"]

                        return commands .when_mentioned_or (prefix ,'')(self ,message )
                    else :

                        data =await getConfig (guild_id )
                        prefix =data ["prefix"]
                        return commands .when_mentioned_or (prefix )(self ,message )
        else :
            async with aiosqlite .connect ('db/np.db')as db :
                async with db .execute ("SELECT id FROM np WHERE id = ?",(message .author .id ,))as cursor :
                    row =await cursor .fetchone ()
                    if row :

                        return commands .when_mentioned_or ('>','')(self ,message )
                    else :

                        return commands .when_mentioned_or ('')(self ,message )


    async def on_message_edit (self ,before ,after ):
        ctx :Context =await self .get_context (after ,cls =Context )
        if before .content !=after .content :
            if after .guild is None or after .author .bot :
                return 
            if ctx .command is None :
                return 
            if type (ctx .channel )=="public_thread":
                return 
            await self .invoke (ctx )
        else :
            return 




def setup_bot ():
    intents =discord .Intents .all ()
    bot =Strelizia (intents =intents )
    return bot 

"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
