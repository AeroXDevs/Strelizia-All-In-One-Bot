

import discord 
from discord .ext import commands 

class _ai (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    """AI commands"""

    def help_custom (self ):
        emoji ='<:Ai:1375898214087135263>'
        label ="AI Commands"
        description =""
        return emoji ,label ,description 

    @commands .group ()
    async def __AI__ (self ,ctx :commands .Context ):
        """`ai activate`, `ai deactivate`, `ai analyze`, `ai analyse`, `ai code`, `ai explain`, `ai conversation-clear`, `ai mood-analyzer`, `ai personality`, `ai conversation-stats`, `ai summarize`, `ai ask`, `ai fact`, `ai database-clear`, `ai roleplay-enable`, `ai roleplay-disable`"""
        pass 
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
