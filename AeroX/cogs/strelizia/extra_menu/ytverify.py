import discord 
from discord .ext import commands 


class YTVerifyHelp (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    """YouTube Verification commands"""

    def help_custom (self ):
        emoji ='<:youtube:1387479173890572323>'
        label ="YouTube Verification"
        description =""
        return emoji ,label ,description 

    @commands .group ()
    async def __YouTubeVerification__ (self ,ctx :commands .Context ):
        """`ytverify setup` , `ytverify channel` , `ytverify role` , `ytverify toggle` , `ytverify reset` , `ytverify config` , `ytverify test` , `ytverify verify`"""

async def setup (client ):
    await client .add_cog (YTVerifyHelp (client ))

"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""