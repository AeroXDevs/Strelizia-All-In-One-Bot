

import discord 
from discord .ext import commands 

class _crew (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    """Staff commands"""

    def help_custom (self ):
        emoji ='<:staff_icons:1381539824711766046>'
        label ="Staff Commands"
        description =""
        return emoji ,label ,description 

    @commands .group ()
    async def __Staff__ (self ,ctx :commands .Context ):
        """`crew`, `crew setup`, `crew clear`, `crew apply`, `crew enable`, `crew disable`, `crew status`
        """
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
