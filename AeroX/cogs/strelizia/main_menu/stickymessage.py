import discord 
from discord .ext import commands 


class __sticky (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    """Sticky commands"""

    def help_custom (self ):
              emoji ='<:sticky:1396894496519884851>'
              label ="Sticky Commands"
              description =""
              return emoji ,label ,description 

    @commands .group ()
    async def __Sticky__ (self ,ctx :commands .Context ):
        """`sticky setup` , `sticky remove` , `sticky list` , `sticky toggle` , `sticky edit` , `sticky config`"""
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
