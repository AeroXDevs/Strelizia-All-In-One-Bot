import discord 

from discord .ext import commands 

import aiosqlite 

class Unblacklist (commands .Cog ):

    def __init__ (self ,bot ):

        self .bot =bot 

        self .db_path ="db/block.db"

    @commands .command (name ="unblacklist")

    @commands .is_owner ()

    async def unblacklist (self ,ctx ,guild_id :int ):

        """Unblacklist a guild by ID. Owner-only."""

        async with aiosqlite .connect (self .db_path )as db :

            await db .execute ("DELETE FROM guild_blacklist WHERE guild_id = ?",(guild_id ,))

            changes =db .total_changes 

            await db .commit ()

        if changes :

            await ctx .send (f"<:icon_tick:1372375089668161597> Unblacklisted guild with ID: `{guild_id}`")

        else :

            await ctx .send (f"<:icon_cross:1372375094336425986> No blacklisted guild found with ID: `{guild_id}`")

async def setup (bot ):

    await bot .add_cog (Unblacklist (bot ))
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
