import discord 
from discord .ext import commands 


class _welcome (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    """Welcome commands"""

    def help_custom (self ):
		      emoji ='<:icon_welcome:1372375051483218071>'
		      label ="Welcomer Commands"
		      description =""
		      return emoji ,label ,description 

    @commands .group ()
    async def __Welcomer__ (self ,ctx :commands .Context ):
        """`greet setup` , `greet reset`, `greet channel` , `greet edit` , `greet test` , `greet config` , `greet autodeletete` , `greet`"""
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
