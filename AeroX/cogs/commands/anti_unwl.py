import discord 
from discord .ext import commands 
import aiosqlite 
from utils .Tools import *


class Unwhitelist (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 
        self .bot .loop .create_task (self .initialize_db ())


    async def initialize_db (self ):
        self .db =await aiosqlite .connect ('db/anti.db')

    @commands .hybrid_command (name ='unwhitelist',aliases =['unwl'],help ="Unwhitelist a user from antinuke")
    @commands .has_permissions (administrator =True )
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,10 ,commands .BucketType .user )
    @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
    @commands .guild_only ()
    async def unwhitelist (self ,ctx ,member :discord .Member =None ):
        if ctx .guild .member_count <2 :
            embed =discord .Embed (
            color =0x08ff00 ,
            description ="<:icon_cross:1372375094336425986> | Your Server Doesn't Meet My 30 Member Criteria"
            )
            return await ctx .send (embed =embed )

        async with self .db .execute (
        "SELECT owner_id FROM extraowners WHERE guild_id = ? AND owner_id = ?",
        (ctx .guild .id ,ctx .author .id )
        )as cursor :
            check =await cursor .fetchone ()

        async with self .db .execute (
        "SELECT status FROM antinuke WHERE guild_id = ?",
        (ctx .guild .id ,)
        )as cursor :
            antinuke =await cursor .fetchone ()

        is_owner =ctx .author .id ==ctx .guild .owner_id 
        if not is_owner and not check :
            embed =discord .Embed (title ="<:icon_cross:1372375094336425986> | Access Denied",
            color =0x08ff00 ,
            description ="Only Server Owner or Extra Owner can Run this Command!"
            )
            return await ctx .send (embed =embed )

        if not antinuke or not antinuke [0 ]:
            embed =discord .Embed (
            color =0x08ff00 ,
            description =(
            f"**{ctx.guild.name} Security Settings <:icon_stagemoderator:1337295812102721577>\n"
            "Ohh NO! looks like your server doesn't enabled security\n\n"
            "Current Status : <:disable_no:1372374999310274600><:enable_yes:1372375008441143417>\n\n"
            "To enable use `antinuke enable` **"
            )
            )
            return await ctx .send (embed =embed )

        if not member :
            embed =discord .Embed (
            color =0x08ff00 ,
            title ="__**Unwhitelist Commands**__",
            description ="**Removes user from whitelisted users which means that the antinuke module will now take actions on them if they trigger it.**"
            )
            embed .add_field (name ="__**Usage**__",value ="<:red_dot:1372500011669258281> `unwhitelist @user/id`\n<:red_dot:1372500011669258281> `unwl @user`")
            return await ctx .send (embed =embed )

        async with self .db .execute (
        "SELECT * FROM whitelisted_users WHERE guild_id = ? AND user_id = ?",
        (ctx .guild .id ,member .id )
        )as cursor :
            data =await cursor .fetchone ()

        if not data :
            embed =discord .Embed (color =0x000000 ,
            description =f"<@{member.id}> is not a whitelisted member."
            )
            return await ctx .send (embed =embed )

        await self .db .execute (
        "DELETE FROM whitelisted_users WHERE guild_id = ? AND user_id = ?",
        (ctx .guild .id ,member .id )
        )
        await self .db .commit ()

        embed =discord .Embed (title ="<:icon_tick:1372375089668161597>Success",
        color =0x000000 ,
        description =f"User <@!{member.id}> has been removed from the whitelist."
        )
        await ctx .send (embed =embed )


"""
@Author: Aegis
    + Discord: Solcodez
    + Community: https://discord.strelix.xyz (AeroX Development)
    + for any queries reach out Community or DM me.
"""
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
