from __future__ import annotations 
import discord 
import asyncio 
import logging 
import aiosqlite 
import json 
from discord .ext import commands 
from utils .Tools import *
from discord .ext .commands import Context 
from discord import app_commands 
import time 
import datetime 
import re 
from typing import *
from time import strftime 
from core import Cog ,Strelizia ,Context 

logging .basicConfig (
level =logging .INFO ,
format ="\x1b[38;5;197m[\x1b[0m%(asctime)s\x1b[38;5;197m]\x1b[0m -> \x1b[38;5;197m%(message)s\x1b[0m",
datefmt ="%H:%M:%S",
)

class Booster (Cog ):
    def __init__ (self ,bot :Strelizia ):
        self .bot =bot 
        self .color =0x000000 
        self .db_path ="db/boost.db"
        self .bot .loop .create_task (self .setup_database ())


        self .url_pattern =re .compile (
        r'^(?:http|ftp)s?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$',re .IGNORECASE 
        )


    def help_custom (self ):
        emoji ="<:icons_nitroboost:1396900839536201829>"
        label ="Booster"
        description ="Setup boost messages and roles for server boosters"
        return emoji ,label ,description 
    async def setup_database (self ):
        """Initialize boost database tables"""
        async with aiosqlite .connect (self .db_path )as db :
            await db .execute ("""
                CREATE TABLE IF NOT EXISTS boost_config (
                    guild_id INTEGER PRIMARY KEY,
                    config TEXT NOT NULL
                )
            """)
            await db .commit ()

    async def get_boost_config (self ,guild_id :int )->dict :
        """Get boost configuration for a guild"""
        async with aiosqlite .connect (self .db_path )as db :
            async with db .execute ("SELECT config FROM boost_config WHERE guild_id = ?",(guild_id ,))as cursor :
                row =await cursor .fetchone ()
                if row :
                    return json .loads (row [0 ])


                default_config ={
                "boost":{
                "channel":[],
                "message":"{user.mention} just boosted {server.name}! 🎉",
                "embed":True ,
                "ping":False ,
                "image":"",
                "thumbnail":"",
                "autodel":0 
                },
                "boost_roles":{
                "roles":[]
                }
                }
                await self .update_boost_config (guild_id ,default_config )
                return default_config 

    async def update_boost_config (self ,guild_id :int ,config :dict ):
        """Update boost configuration for a guild"""
        async with aiosqlite .connect (self .db_path )as db :
            await db .execute (
            "INSERT OR REPLACE INTO boost_config (guild_id, config) VALUES (?, ?)",
            (guild_id ,json .dumps (config ))
            )
            await db .commit ()

    def is_authorized (self ,ctx )->bool :
        """Check if user is authorized to use admin commands"""
        return (
        ctx .author ==ctx .guild .owner 
        or ctx .author .guild_permissions .administrator 
        or ctx .author .top_role .position >=ctx .guild .me .top_role .position 
        )


    def format_boost_message (self ,message :str ,user :discord .Member ,guild :discord .Guild )->str :
        """Format boost message with new variable style"""
        replacements ={

        "{server.name}":guild .name ,
        "{server.id}":str (guild .id ),
        "{server.owner}":str (guild .owner ),
        "{server.icon}":guild .icon .url if guild .icon else "",
        "{server.boost_count}":str (guild .premium_subscription_count ),
        "{server.boost_level}":f"Level {guild.premium_tier}",
        "{server.member_count}":str (guild .member_count ),


        "{user.name}":user .display_name ,
        "{user.mention}":user .mention ,
        "{user.tag}":str (user ),
        "{user.id}":str (user .id ),
        "{user.avatar}":user .display_avatar .url ,
        "{user.created_at}":f"<t:{int(user.created_at.timestamp())}:F>",
        "{user.joined_at}":f"<t:{int(user.joined_at.timestamp())}:F>"if user .joined_at else "Unknown",
        "{user.top_role}":user .top_role .name if user .top_role else "None",
        "{user.is_booster}":str (bool (user .premium_since )),
        "{user.is_mobile}":str (user .is_on_mobile ()),
        "{user.boosted_at}":f"<t:{int(user.premium_since.timestamp())}:F>"if user .premium_since else "Unknown"
        }


        for old ,new in replacements .items ():
            message =message .replace (old ,new )

        return message 

    async def send_permission_error (self ,ctx ):
        """Send permission error embed"""
        embed =discord .Embed (
        description ="```diff\n- You must have Administrator permission.\n- Your top role should be above my top role.\n```",
        color =self .color 
        )
        embed .set_author (name =ctx .author .name ,icon_url =ctx .author .display_avatar .url )
        await ctx .send (embed =embed )

    @commands .group (name ="boost",aliases =['bst'],invoke_without_command =True ,help ="Boost message configuration commands")
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,5 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    @commands .has_permissions (administrator =True )
    async def _boost (self ,ctx ):
        if ctx .subcommand_passed is None :
            await ctx .send_help (ctx .command )
            ctx .command .reset_cooldown (ctx )

    @_boost .command (name ="thumbnail",help ="Set boost message thumbnail")
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,2 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    @commands .has_permissions (administrator =True )
    async def _boost_thumbnail (self ,ctx ,thumbnail_url :str ):
        if not self .is_authorized (ctx ):
            await self .send_permission_error (ctx )
            return 

        if not self .url_pattern .match (thumbnail_url ):
            await ctx .send (embed =discord .Embed (
            description ="<:icon_cross:1372375094336425986> Please provide a valid URL.",
            color =self .color 
            ))

            return 

        data =await self .get_boost_config (ctx .guild .id )
        data ["boost"]["thumbnail"]=thumbnail_url 
        await self .update_boost_config (ctx .guild .id ,data )

        embed =discord .Embed (
        color =self .color ,
        description ="<:icon_tick:1372375089668161597> Successfully updated the boost thumbnail URL.",
        timestamp =ctx .message .created_at 
        )
        embed .set_author (name =ctx .author .name ,icon_url =ctx .author .display_avatar .url )
        await ctx .send (embed =embed )

    @_boost .command (name ="image",help ="Set boost message image")
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,2 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    @commands .has_permissions (administrator =True )
    async def _boost_image (self ,ctx ,*,image_url :str ):
        if not self .is_authorized (ctx ):
            await self .send_permission_error (ctx )
            return 

        if not self .url_pattern .match (image_url ):
            await ctx .send (embed =discord .Embed (
            description ="<:icon_cross:1372375094336425986> Please provide a valid URL.",
            color =self .color 
            ))

            return 

        data =await self .get_boost_config (ctx .guild .id )
        data ["boost"]["image"]=image_url 
        await self .update_boost_config (ctx .guild .id ,data )

        embed =discord .Embed (
        color =self .color ,
        description ="<:icon_tick:1372375089668161597> Successfully updated the boost image URL.",
        timestamp =ctx .message .created_at 
        )
        embed .set_author (name =ctx .author .name ,icon_url =ctx .author .display_avatar .url )
        await ctx .send (embed =embed )

    @_boost .command (name ="autodel",help ="Set auto-delete timer for boost messages (0 to disable)")
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,2 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    @commands .has_permissions (administrator =True )
    async def _boost_autodel (self ,ctx ,seconds :int ):
        if not self .is_authorized (ctx ):
            await self .send_permission_error (ctx )
            return 

        if seconds <0 :
            await ctx .send (embed =discord .Embed (
            description ="<:icon_cross:1372375094336425986> Auto-delete timer must be 0 or greater.",
            color =self .color 
            ))

            return 

        data =await self .get_boost_config (ctx .guild .id )
        data ["boost"]["autodel"]=seconds 
        await self .update_boost_config (ctx .guild .id ,data )

        description =f"<:icon_tick:1372375089668161597> Successfully set auto-delete timer to {seconds} seconds."
        if seconds ==0 :
            description ="<:icon_tick:1372375089668161597> Auto-delete has been disabled."

        embed =discord .Embed (
        color =self .color ,
        description =description ,
        timestamp =ctx .message .created_at 
        )
        embed .set_author (name =ctx .author .name ,icon_url =ctx .author .display_avatar .url )
        await ctx .send (embed =embed )

    @_boost .command (name ="message",help ="Set boost message content")
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,2 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    @commands .has_permissions (administrator =True )
    async def _boost_message (self ,ctx ):
        if not self .is_authorized (ctx ):
            await self .send_permission_error (ctx )
            return 

        embed =discord .Embed (
        color =self .color ,
        title ="<:icon_tick:1372375089668161597> Boost Message Setup",
        description ="Send your boost message in this channel now.\n\n**Available Variables:**\n"
        "```\n"
        "{server.name}         - Server name\n"
        "{server.id}           - Server ID\n"
        "{server.owner}        - Server owner\n"
        "{server.icon}         - Server icon URL\n"
        "{server.boost_count}  - Current boost count\n"
        "{server.boost_level}  - Boost level (e.g., Level 2)\n"
        "{server.member_count} - Total member count\n\n"
        "{user.name}        - Booster's display name\n"
        "{user.mention}     - Mention the booster\n"
        "{user.tag}         - Booster's full tag\n"
        "{user.id}          - Booster's ID\n"
        "{user.avatar}      - Booster's avatar URL\n"
        "{user.created_at}  - When the account was created\n"
        "{user.joined_at}   - When user joined the server\n"
        "{user.top_role}    - Booster's top role name\n"
        "{user.is_booster}  - Whether they’re a booster\n"
        "{user.is_mobile}   - Whether on mobile\n"
        "{user.boosted_at}  - Boost timestamp\n"
        "```"
        )
        embed .set_footer (text ="You have 60 seconds to respond")
        await ctx .send (embed =embed )

        def check (m ):
            return m .author ==ctx .author and m .channel ==ctx .channel 

        try :
            message =await self .bot .wait_for ('message',check =check ,timeout =60.0 )
        except asyncio .TimeoutError :
            await ctx .send (embed =discord .Embed (
            description ="<:icon_timer:1372376119838695435> Timeout! Please try again.",
            color =self .color 
            ))

            return 

        data =await self .get_boost_config (ctx .guild .id )
        data ["boost"]["message"]=message .content 
        await self .update_boost_config (ctx .guild .id ,data )

        embed =discord .Embed (
        color =self .color ,
        description ="<:icon_tick:1372375089668161597> Successfully updated the boost message.",
        timestamp =ctx .message .created_at 
        )
        embed .set_author (name =ctx .author .name ,icon_url =ctx .author .display_avatar .url )
        await ctx .send (embed =embed )

    @_boost .command (name ="embed",help ="Toggle embed formatting for boost messages")
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,2 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    @commands .has_permissions (administrator =True )
    async def _boost_embed (self ,ctx ):
        if not self .is_authorized (ctx ):
            await self .send_permission_error (ctx )
            return 

        data =await self .get_boost_config (ctx .guild .id )
        data ["boost"]["embed"]=not data ["boost"]["embed"]
        await self .update_boost_config (ctx .guild .id ,data )

        status ="enabled"if data ["boost"]["embed"]else "disabled"
        embed =discord .Embed (
        color =self .color ,
        description =f"<:icon_tick:1372375089668161597> Embed formatting has been **{status}**.",
        timestamp =ctx .message .created_at 
        )
        embed .set_author (name =ctx .author .name ,icon_url =ctx .author .display_avatar .url )
        await ctx .send (embed =embed )

    @_boost .command (name ="ping",help ="Toggle pinging the booster")
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,2 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    @commands .has_permissions (administrator =True )
    async def _boost_ping (self ,ctx ):
        if not self .is_authorized (ctx ):
            await self .send_permission_error (ctx )
            return 

        data =await self .get_boost_config (ctx .guild .id )
        data ["boost"]["ping"]=not data ["boost"]["ping"]
        await self .update_boost_config (ctx .guild .id ,data )

        status ="enabled"if data ["boost"]["ping"]else "disabled"
        embed =discord .Embed (
        color =self .color ,
        description =f"<:icon_tick:1372375089668161597> Booster pinging has been **{status}**.",
        timestamp =ctx .message .created_at 
        )
        embed .set_author (name =ctx .author .name ,icon_url =ctx .author .display_avatar .url )
        await ctx .send (embed =embed )

    @_boost .group (name ="channel",help ="Manage boost notification channels")
    @blacklist_check ()
    @ignore_check ()
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    @commands .has_permissions (administrator =True )
    async def _boost_channel (self ,ctx ):
        if ctx .subcommand_passed is None :
            await ctx .send_help (ctx .command )
            ctx .command .reset_cooldown (ctx )

    @_boost_channel .command (name ="add",help ="Add a boost notification channel")
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    @commands .has_permissions (administrator =True )
    async def _boost_channel_add (self ,ctx ,channel :discord .TextChannel ):
        if not self .is_authorized (ctx ):
            await self .send_permission_error (ctx )
            return 

        data =await self .get_boost_config (ctx .guild .id )
        channels =data ["boost"]["channel"]

        if len (channels )>=3 :
            embed =discord .Embed (
            color =self .color ,
            description ="<:icon_cross:1372375094336425986> Maximum boost channel limit reached (3 channels).",
            timestamp =ctx .message .created_at 
            )
            embed .set_author (name =ctx .author .name ,icon_url =ctx .author .display_avatar .url )
            await ctx .send (embed =embed )
            return 

        if str (channel .id )in channels :
            embed =discord .Embed (
            color =self .color ,
            description ="<:icon_cross:1372375094336425986> This channel is already in the boost channels list.",
            timestamp =ctx .message .created_at 
            )
            embed .set_author (name =ctx .author .name ,icon_url =ctx .author .display_avatar .url )
            await ctx .send (embed =embed )
            return 

        channels .append (str (channel .id ))
        await self .update_boost_config (ctx .guild .id ,data )

        embed =discord .Embed (
        color =self .color ,
        description =f"<:icon_tick:1372375089668161597> Successfully added {channel.mention} to boost channels list.",
        timestamp =ctx .message .created_at 
        )
        embed .set_author (name =ctx .author .name ,icon_url =ctx .author .display_avatar .url )
        await ctx .send (embed =embed )

    @_boost_channel .command (name ="remove",help ="Remove a boost notification channel")
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    @commands .has_permissions (administrator =True )
    async def _boost_channel_remove (self ,ctx ,channel :discord .TextChannel ):
        if not self .is_authorized (ctx ):
            await self .send_permission_error (ctx )
            return 

        data =await self .get_boost_config (ctx .guild .id )
        channels =data ["boost"]["channel"]

        if not channels :
            embed =discord .Embed (
            color =self .color ,
            description ="<:icon_cross:1372375094336425986> No boost channels are currently set up.",
            timestamp =ctx .message .created_at 
            )
            embed .set_author (name =ctx .author .name ,icon_url =ctx .author .display_avatar .url )
            await ctx .send (embed =embed )
            return 

        if str (channel .id )not in channels :
            embed =discord .Embed (
            color =self .color ,
            description ="<:icon_cross:1372375094336425986> This channel is not in the boost channels list.",
            timestamp =ctx .message .created_at 
            )
            embed .set_author (name =ctx .author .name ,icon_url =ctx .author .display_avatar .url )
            await ctx .send (embed =embed )
            return 

        channels .remove (str (channel .id ))
        await self .update_boost_config (ctx .guild .id ,data )

        embed =discord .Embed (
        color =self .color ,
        description =f"<:icon_tick:1372375089668161597> Successfully removed {channel.mention} from boost channels list.",
        timestamp =ctx .message .created_at 
        )
        embed .set_author (name =ctx .author .name ,icon_url =ctx .author .display_avatar .url )
        await ctx .send (embed =embed )

    @_boost .command (name ="test",help ="Test how the boost message will look")
    @blacklist_check ()
    @ignore_check ()
    @commands .guild_only ()
    @commands .has_permissions (administrator =True )
    async def _boost_test (self ,ctx ):
        data =await self .get_boost_config (ctx .guild .id )
        channels =data ["boost"]["channel"]

        if not channels :
            embed =discord .Embed (
            color =self .color ,
            description ="<:icon_cross:1372375094336425986> Please set up a boost channel first using `boost channel add #channel`.",
            timestamp =ctx .message .created_at 
            )
            embed .set_author (name =ctx .author .name ,icon_url =ctx .author .display_avatar .url )
            await ctx .send (embed =embed )
            return 


        formatted_message =self .format_boost_message (data ["boost"]["message"],ctx .author ,ctx .guild )


        channel =self .bot .get_channel (int (channels [0 ]))
        if not channel :
            await ctx .send (embed =discord .Embed (
            description ="<:icon_cross:1372375094336425986> The configured boost channel no longer exists.",
            color =self .color 
            ))

            return 

        try :
            if data ["boost"]["embed"]:
                embed =discord .Embed (description =formatted_message ,color =self .color )
                embed .set_author (name =ctx .author .display_name ,icon_url =ctx .author .display_avatar .url )
                embed .timestamp =discord .utils .utcnow ()

                if data ["boost"]["image"]:
                    embed .set_image (url =data ["boost"]["image"])

                if data ["boost"]["thumbnail"]:
                    embed .set_thumbnail (url =data ["boost"]["thumbnail"])

                if ctx .guild .icon :
                    embed .set_footer (text =ctx .guild .name ,icon_url =ctx .guild .icon .url )

                ping_content =ctx .author .mention if data ["boost"]["ping"]else ""
                await channel .send (ping_content ,embed =embed )
            else :
                await channel .send (formatted_message )

        except discord .Forbidden :
            await ctx .send (embed =discord .Embed (
            description ="<:icon_cross:1372375094336425986> I don't have permission to send messages in the boost channel.",
            color =self .color 
            ))

        except Exception as e :
            await ctx .send (embed =discord .Embed (
            description =f"<:icon_cross:1372375094336425986> An error occurred: `{str(e)}`",
            color =self .color 
            ))


    @_boost .command (name ="config",help ="View current boost configuration")
    @blacklist_check ()
    @ignore_check ()
    @commands .has_permissions (administrator =True )
    async def _boost_config (self ,ctx ):
        data =await self .get_boost_config (ctx .guild .id )
        channels =data ["boost"]["channel"]

        if not channels :
            await ctx .send (embed =discord .Embed (
            description ="<:icon_cross:1372375094336425986> Please set up a boost channel first using `boost channel add #channel`.",
            color =self .color 
            ))

            return 

        embed =discord .Embed (
        color =self .color ,
        title =f"<:icons_nitroboost:1396900839536201829> Boost Configuration for {ctx.guild.name}"
        )


        channel_mentions =[]
        for channel_id in channels :
            channel =self .bot .get_channel (int (channel_id ))
            if channel :
                channel_mentions .append (channel .mention )

        embed .add_field (
        name ="Channels",
        value ="\n".join (channel_mentions )if channel_mentions else "None",
        inline =False 
        )

        embed .add_field (
        name ="Message",
        value =f"```{data['boost']['message']}```",
        inline =False 
        )

        embed .add_field (
        name ="Embed",
        value ="<:icon_tick:1372375089668161597> Enabled"if data ["boost"]["embed"]else "<:icon_cross:1372375094336425986> Disabled",
        inline =True 
        )

        embed .add_field (
        name ="Ping",
        value ="<:icon_tick:1372375089668161597> Enabled"if data ["boost"]["ping"]else "<:icon_cross:1372375094336425986> Disabled",
        inline =True 
        )

        embed .add_field (
        name ="Auto-delete",
        value =f"{data['boost']['autodel']}s"if data ["boost"]["autodel"]else "Disabled",
        inline =True 
        )

        if ctx .guild .icon :
            embed .set_footer (text =ctx .guild .name ,icon_url =ctx .guild .icon .url )
            embed .set_thumbnail (url =ctx .guild .icon .url )

        await ctx .send (embed =embed )

    @_boost .command (name ="reset",help ="Reset boost configuration")
    @commands .cooldown (1 ,5 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    @blacklist_check ()
    @ignore_check ()
    @commands .has_permissions (administrator =True )
    async def _boost_reset (self ,ctx ):
        if not self .is_authorized (ctx ):
            await self .send_permission_error (ctx )
            return 

        data =await self .get_boost_config (ctx .guild .id )

        if not data ["boost"]["channel"]:
            embed =discord .Embed (
            description ="<:icon_cross:1372375094336425986> No boost configuration found to reset.",
            color =self .color 
            )
            await ctx .send (embed =embed )
            return 


        data ["boost"]["channel"]=[]
        data ["boost"]["image"]=""
        data ["boost"]["message"]="{user.mention} just boosted {server.name}! 🎉"
        data ["boost"]["thumbnail"]=""
        data ["boost"]["embed"]=True 
        data ["boost"]["ping"]=False 
        data ["boost"]["autodel"]=0 

        await self .update_boost_config (ctx .guild .id ,data )

        embed =discord .Embed (
        description ="<:icon_tick:1372375089668161597> Successfully reset all boost configuration.",
        color =self .color 
        )
        await ctx .send (embed =embed )

    @commands .group (name ="boostrole",invoke_without_command =True ,help ="Manage boost roles")
    @commands .cooldown (1 ,5 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @blacklist_check ()
    @ignore_check ()
    @commands .guild_only ()
    @commands .has_permissions (administrator =True )
    async def _boostrole (self ,ctx ):
        if ctx .subcommand_passed is None :
            await ctx .send_help (ctx .command )
            ctx .command .reset_cooldown (ctx )

    @_boostrole .command (name ="config",help ="View boost role configuration")
    @commands .cooldown (1 ,5 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    @blacklist_check ()
    @ignore_check ()
    @commands .has_permissions (administrator =True )
    async def _boostrole_config (self ,ctx ):
        data =await self .get_boost_config (ctx .guild .id )
        role_ids =data ["boost_roles"]["roles"]

        if not role_ids :
            embed =discord .Embed (
            color =self .color ,
            title =f"Boost Roles - {ctx.guild.name}",
            description ="No boost roles configured."
            )
            await ctx .send (embed =embed )
            return 

        roles =[]
        for role_id in role_ids :
            role =ctx .guild .get_role (int (role_id ))
            if role :
                roles .append (role .mention )

        embed =discord .Embed (
        color =self .color ,
        title =f"Boost Roles - {ctx.guild.name}"
        )
        embed .add_field (
        name ="Roles",
        value ="\n".join (roles )if roles else "No valid roles found",
        inline =False 
        )
        await ctx .send (embed =embed )

    @_boostrole .command (name ="add",help ="Add a boost role")
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    @commands .has_permissions (administrator =True )
    async def _boostrole_add (self ,ctx ,role :discord .Role ):
        if not self .is_authorized (ctx ):
            await self .send_permission_error (ctx )
            return 

        data =await self .get_boost_config (ctx .guild .id )
        roles =data ["boost_roles"]["roles"]

        if len (roles )>=10 :
            embed =discord .Embed (
            description ="<:icon_cross:1372375094336425986> Maximum boost role limit reached (10 roles).",
            color =self .color 
            )
            await ctx .send (embed =embed )
            return 

        if str (role .id )in roles :
            embed =discord .Embed (
            description =f"<:icon_cross:1372375094336425986> {role.mention} is already a boost role.",
            color =self .color 
            )
            await ctx .send (embed =embed )
            return 

        roles .append (str (role .id ))
        await self .update_boost_config (ctx .guild .id ,data )

        embed =discord .Embed (
        description =f"<:icon_tick:1372375089668161597> {role.mention} has been added as a boost role.",
        color =self .color 
        )
        await ctx .send (embed =embed )

    @_boostrole .command (name ="remove",help ="Remove a boost role")
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    @commands .has_permissions (administrator =True )
    async def _boostrole_remove (self ,ctx ,role :discord .Role ):
        if not self .is_authorized (ctx ):
            await self .send_permission_error (ctx )
            return 

        data =await self .get_boost_config (ctx .guild .id )
        roles =data ["boost_roles"]["roles"]

        if not roles :
            embed =discord .Embed (
            description ="<:icon_cross:1372375094336425986> No boost roles are currently configured.",
            color =self .color 
            )
            await ctx .send (embed =embed )
            return 

        if str (role .id )not in roles :
            embed =discord .Embed (
            description =f"<:icon_cross:1372375094336425986> {role.mention} is not a boost role.",
            color =self .color 
            )
            await ctx .send (embed =embed )
            return 

        roles .remove (str (role .id ))
        await self .update_boost_config (ctx .guild .id ,data )

        embed =discord .Embed (
        description =f"<:icon_tick:1372375089668161597> {role.mention} has been removed from boost roles.",
        color =self .color 
        )
        await ctx .send (embed =embed )

    @_boostrole .command (name ="reset",help ="Reset boost role configuration")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    @blacklist_check ()
    @ignore_check ()
    @commands .has_permissions (administrator =True )
    async def _boostrole_reset (self ,ctx ):
        if not self .is_authorized (ctx ):
            await self .send_permission_error (ctx )
            return 

        data =await self .get_boost_config (ctx .guild .id )

        if not data ["boost_roles"]["roles"]:
            embed =discord .Embed (
            description ="<:icon_cross:1372375094336425986> No boost roles are currently configured.",
            color =self .color 
            )
            await ctx .send (embed =embed )
            return 

        data ["boost_roles"]["roles"]=[]
        await self .update_boost_config (ctx .guild .id ,data )

        embed =discord .Embed (
        description ="<:icon_tick:1372375089668161597> Successfully cleared all boost roles.",
        color =self .color 
        )
        await ctx .send (embed =embed )

async def setup (bot ):
    await bot .add_cog (Booster (bot ))