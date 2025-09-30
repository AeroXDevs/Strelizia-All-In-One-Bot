import discord 
from discord .ext import commands 


class _music (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    """Music commands"""

    def help_custom (self ):
              emoji ='<:icon_music:1372375041542721638>'
              label ="Music Commands"
              description =""
              return emoji ,label ,description 

    @commands .group ()
    async def __Music__ (self ,ctx :commands .Context ):
        """`play`, `search`, `nowplaying`, `autoplay`, `loop`, `pause`, `resume`, `skip`, `shuffle`, `stop`, `volume`, `queue`, `clearqueue`, `replay`, `join`, `disconnect`, `seek`, `remove`, `move`, `lyrics`, `twentyfourseven`
\n__Slash Commands__\n
`music`, `music play`, `music search`, `music nowplaying`, `music autoplay`, `music loop`, `music pause`, `music resume`, `music skip`, `music shuffle`, `music stop`, `music volume`, `music queue`, `music clearqueue`, `music replay`, `music join`, `music disconnect`, `music seek`, `music remove`, `music move`, `music lyrics`, `music twentyfourseven`"""
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
