

import discord 
from discord .ext import commands 

class _counting (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    """Counting commands"""

    def help_custom (self ):
        emoji ='<:plus_icons:1377949309751791717>'
        label ="Counting Commands"
        description =""
        return emoji ,label ,description 

    @commands .group ()
    async def __COUNTING__ (self ,ctx :commands .Context ):
        """`counting config` , `counting enable` , `counting disable` , `counting channel` , `counting reset` , `counting leaderboard` , `counting global` , `counting stats` , `counting achievements` , `counting info`
        """
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
