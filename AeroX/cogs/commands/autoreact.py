import discord 
from discord .ext import commands 
import aiosqlite 
import re 
from utils .Tools import *

class AutoReaction (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 
        self .db_path ='db/autoreact.db'
        self .bot .loop .create_task (self .setup_database ())

    async def setup_database (self ):
        async with aiosqlite .connect (self .db_path )as db :
            await db .execute ("""
                CREATE TABLE IF NOT EXISTS autoreact (
                    guild_id INTEGER,
                    trigger TEXT,
                    emojis TEXT
                )
            """)
            await db .commit ()

    async def get_triggers (self ,guild_id ):
        async with aiosqlite .connect (self .db_path )as db :
            cursor =await db .execute ("SELECT trigger, emojis FROM autoreact WHERE guild_id = ?",(guild_id ,))
            return await cursor .fetchall ()

    async def trigger_exists (self ,guild_id ,trigger ):
        async with aiosqlite .connect (self .db_path )as db :
            cursor =await db .execute ("SELECT 1 FROM autoreact WHERE guild_id = ? AND trigger = ?",(guild_id ,trigger ))
            return await cursor .fetchone ()

    @commands .group (name ="react",aliases =["autoreact"],help ="Lists all subcommands of autoreact group.",invoke_without_command =True )
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,4 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    @commands .has_permissions (administrator =True )
    async def react (self ,ctx ):
        if ctx .subcommand_passed is None :
            await ctx .send_help (ctx .command )
            ctx .command .reset_cooldown (ctx )

    @react .command (name ="add",aliases =["set","create"],help ="Adds a trigger and its emojis to the autoreact.")
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,4 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    @commands .has_permissions (administrator =True )
    async def add (self ,ctx ,trigger :str ,*,emojis :str ):
        if len (trigger .split ())>1 :
            embed =discord .Embed (
            title ="<:icon_cross:1372375094336425986> | Invalid Trigger",
            description ="Triggers can only be one word.",
            color =0x000000 
            )
            embed .set_footer (text =f"Requested By {ctx.author}",
            icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
            return await ctx .reply (embed =embed )


        emoji_list =re .findall (r"<a?:\w+:\d+>|[\u263a-\U0001f645]",emojis )
        if len (emoji_list )>10 :
            embed =discord .Embed (
            title ="<:icon_cross:1372375094336425986> | Too Many Emojis",
            description ="You can only set up to **10** emojis per trigger.",
            color =0x000000 
            )
            embed .set_footer (text =f"Requested By {ctx.author}",
            icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
            return await ctx .reply (embed =embed )

        triggers =await self .get_triggers (ctx .guild .id )
        if len (triggers )>=10 :
            embed =discord .Embed (
            title ="<:icon_danger:1373170993236803688> | Trigger Limit Reached",
            description ="You can only set up to 10 triggers for auto-reactions in this guild.",
            color =0x000000 
            )
            embed .set_footer (text =f"Requested By {ctx.author}",
            icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
            return await ctx .reply (embed =embed )

        if await self .trigger_exists (ctx .guild .id ,trigger ):
            embed =discord .Embed (
            title ="<:icon_danger:1373170993236803688> | Trigger Exists",
            description =f"The trigger '{trigger}' already exists. Remove it before adding it again.",
            color =0x000000 
            )
            embed .set_footer (text =f"Requested By {ctx.author}",
            icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
            return await ctx .reply (embed =embed )

        async with aiosqlite .connect (self .db_path )as db :
            await db .execute ("INSERT INTO autoreact (guild_id, trigger, emojis) VALUES (?, ?, ?)",
            (ctx .guild .id ,trigger ," ".join (emoji_list )))
            await db .commit ()

        embed =discord .Embed (
        title ="<:icon_tick:1372375089668161597>| Trigger Added",
        description =f"Successfully added trigger '{trigger}' with emojis {', '.join(emoji_list)}.",
        color =0x000000 
        )
        embed .set_footer (text =f"Requested By {ctx.author}",
        icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
        await ctx .reply (embed =embed )

    @react .command (name ="remove",aliases =["clear","delete"],help ="Removes a trigger and its emojis from the autoreact.")
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,4 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    @commands .has_permissions (administrator =True )
    async def remove (self ,ctx ,trigger :str ):
        if not await self .trigger_exists (ctx .guild .id ,trigger ):
            embed =discord .Embed (
            title ="<:icon_cross:1372375094336425986> | Trigger Not Found",
            description =f"The trigger '{trigger}' does not exist.",
            color =0x000000 
            )
            embed .set_footer (text =f"Requested By {ctx.author}",
            icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
            return await ctx .reply (embed =embed )

        async with aiosqlite .connect (self .db_path )as db :
            await db .execute ("DELETE FROM autoreact WHERE guild_id = ? AND trigger = ?",(ctx .guild .id ,trigger ))
            await db .commit ()

        embed =discord .Embed (
        title ="<:icon_tick:1372375089668161597>| Trigger Removed",
        description =f"Successfully removed trigger '{trigger}'.",
        color =0x000000 
        )
        embed .set_footer (text =f"Requested By {ctx.author}",
        icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
        await ctx .reply (embed =embed )

    @react .command (name ="list",aliases =["show","config"],help ="Lists all the triggers and their emojis in the autoreact module.")
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,4 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    @commands .has_permissions (administrator =True )
    async def list (self ,ctx ):
        triggers =await self .get_triggers (ctx .guild .id )
        if not triggers :
            embed =discord .Embed (
            title ="No Triggers Set",
            description ="There are no auto-reaction triggers set in this guild.",
            color =0x000000 
            )
            return await ctx .reply (embed =embed )

        trigger_list ="\n".join ([f"{t[0]}: {t[1]}"for t in triggers ])
        embed =discord .Embed (
        title ="Auto-Reaction Triggers",
        description =trigger_list ,
        color =0x000000 
        )
        embed .set_footer (text =f"Requested By {ctx.author}",
        icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
        await ctx .reply (embed =embed )

    @react .command (name ="reset",help ="Resets all the triggers and their emojis in the autoreact module.")
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,4 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    @commands .has_permissions (administrator =True )
    async def reset (self ,ctx ):
        triggers =await self .get_triggers (ctx .guild .id )
        if not triggers :
            embed =discord .Embed (
            title ="<:icon_cross:1372375094336425986> | No Triggers Set",
            description ="There are no auto-reaction triggers set to reset.",
            color =0x000000 
            )
            embed .set_footer (text =f"Requested By {ctx.author}",
            icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
            return await ctx .reply (embed =embed )

        async with aiosqlite .connect (self .db_path )as db :
            await db .execute ("DELETE FROM autoreact WHERE guild_id = ?",(ctx .guild .id ,))
            await db .commit ()

        embed =discord .Embed (
        title ="<:icon_tick:1372375089668161597>| All Triggers Reseted",
        description ="Successfully removed all auto-reaction triggers.",
        color =0x000000 
        )
        embed .set_footer (text =f"Requested By {ctx.author}",
        icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
        await ctx .reply (embed =embed )

async def setup (bot ):
    await bot .add_cog (AutoReaction (bot ))

"""
@Author: Aegis
    + Discord: Solcodez
    + Community: https://discord.strelix.xyz (AeroX Development)
    + for any queries reach out support or DM me.
"""
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
