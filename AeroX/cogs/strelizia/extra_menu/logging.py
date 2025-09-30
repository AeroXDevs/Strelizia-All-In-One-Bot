import discord 
from discord .ext import commands 

class _logging (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    """Logging commands"""

    def help_custom (self ):
		      emoji ='<:logging_icons:1377373741268471900>'
		      label ="Logging Commands"
		      description =""
		      return emoji ,label ,description 

    @commands .group ()
    async def __Logging__ (self ,ctx :commands .Context ):
        """`log`, `log enable`, `log disable`, `log config`, `log ignore`, `log status`, `log toggle`"""
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
