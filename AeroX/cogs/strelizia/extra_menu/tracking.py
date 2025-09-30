

import discord 
from discord .ext import commands 

class _tracking (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    """Tracking commands"""

    def help_custom (self ):
        emoji ='<:tracking_icons:1378293093219962921>'
        label ="Tracking Commands"
        description =""
        return emoji ,label ,description 

    @commands .group ()
    async def __Tracking__ (self ,ctx :commands .Context ):
        """`tracking`, `tracking enable`, `tracking disable`, `tracking status`, `tracking setup`, `tracking wipe`, `tracking export`, `tracking import`, `tracking messages`, `tracking invites`, `tracking leaderboard`, `tracking messagelb`, `tracking dailylb`, `tracking invitelb`, `tracking addmessages`, `tracking resetmessages`, `tracking addinvites`, `tracking resetinvites`, `tracking setlogchannel`, `tracking myinvites`, `tracking resetall`
        """
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
