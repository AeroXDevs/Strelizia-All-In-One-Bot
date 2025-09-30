
import discord 
from discord .ext import commands 

class VerificationHelp (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    """Verification commands help"""

    def help_custom (self ):
        emoji ='<:icon_security:1372375056893739019>'
        label ="Verification Commands"
        description =""
        return emoji ,label ,description 

    @commands .group ()
    async def __Verification__ (self ,ctx :commands .Context ):
        """`verification setup`, `verification status`, `verification enable`, `verification disable`, `verification logs`, `verification reset`, `verification verify`, `verification fix`"""
        pass 

async def setup (bot ):
    await bot .add_cog (VerificationHelp (bot ))

"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
