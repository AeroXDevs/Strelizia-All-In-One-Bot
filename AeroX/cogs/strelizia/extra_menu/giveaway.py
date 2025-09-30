import discord 
from discord .ext import commands 


class _giveaway (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    """Giveaway commands"""

    def help_custom (self ):
		      emoji ='<:icon_giveaway:1372375046332485663>'
		      label ="Giveaway Commands"
		      description =""
		      return emoji ,label ,description 

    @commands .group ()
    async def __Giveaway__ (self ,ctx :commands .Context ):
        """`/giveaway create` , `/giveaway end` , `/giveaway reroll` , `/giveaway list` , `/giveaway template create` , `/giveaway template list` , `/giveaway template delete` , `/giveaway blacklist add` , `/giveaway blacklist remove` , `/giveaway blacklist list`"""
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
