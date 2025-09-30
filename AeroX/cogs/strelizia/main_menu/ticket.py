import discord 
from discord .ext import commands 

class ticket (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    """Ticket Commands"""

    def help_custom (self ):
        emoji ='<:icon_ticket:1372375056893739019>'
        label ="Ticket Commands"
        description =""
        return emoji ,label ,description 

    @commands .group ()
    async def __TICKET__ (self ,ctx :commands .Context ):
        """`ticket` , `ticket setup` , `ticket reset` , `ticket close` , `ticket transcript` , `ticket add` , `ticket remove` , `ticket rename` , `ticket category-add` , `ticket category-remove` , `ticket category-list` , `ticket category-default` , `ticket panel-send` , `ticket claim`
        """
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
