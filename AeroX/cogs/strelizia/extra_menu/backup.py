import discord 

from discord .ext import commands 

class _Backup (commands .Cog ):

    def __init__ (self ,bot ):

        self .bot =bot 

    """Backup commands"""



    def help_custom (self ):

        emoji ='<:backup_icons:1376857941986250844>'

        label ="Backup Commands"

        description =""

        return emoji ,label ,description 

    @commands .group ()

    async def __Backup__ (self ,ctx :commands .Context ):

        """`backup` , `backup create` , `backup list` , `backup delete` , `backup info` , `backup transfer` , `backup preview` , `backup export` , `backup import` , `backup verify` , `backup stats` , `backup load`"""

        if ctx .invoked_subcommand is None :

            await ctx .send_help (ctx .command )
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
