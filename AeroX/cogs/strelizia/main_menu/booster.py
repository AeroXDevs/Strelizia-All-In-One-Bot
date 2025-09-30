import discord 
from discord .ext import commands 


class __boost (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    """Boost commands"""

    def help_custom (self ):
              emoji ='<:icons_nitroboost:1396900839536201829>'
              label ="Boost Commands"
              description =""
              return emoji ,label ,description 

    @commands .group ()
    async def __Boost__ (self ,ctx :commands .Context ):
        """`boost setup` , `boost message` , `boost channel` , `boostrole` , `boost config`"""
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
