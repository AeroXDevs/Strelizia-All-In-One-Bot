
import discord 
from discord .ext import commands 

class RoleplayHelp (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    """Roleplay Help Commands"""

    def help_custom (self ):
        emoji ='<:icons_tv:1381541359055540255>'
        label ="Roleplay Commands"
        description =""
        return emoji ,label ,description 

    @commands .group ()
    async def __Roleplay__ (self ,ctx :commands .Context ):
        """`sys hug` , `sys kiss` , `sys cuddle` , `sys pat` , `sys slap` , `sys tickle` , `sys poke` , `sys wave` , `sys dance` , `sys cry` , `sys laugh` , `sys smile` , `sys blush` , `sys wink` , `sys thumbsup` , `sys clap` , `sys bow` , `sys salute` , `sys facepalm` , `sys shrug` , `sys sleep` , `sys eat` , `sys drink` , `sys run` , `sys lewd` , `sys pout` , `sys sleepy` , `sys smug` , `sys wag` , `sys thinking` , `sys triggered` , `sys teehee` , `sys deredere` , `sys thonking` , `sys scoff` , `sys happy` , `sys thumbs` , `sys grin` , `sys lick` , `sys nom` , `sys stare` , `sys highfive` , `sys bite` , `sys greet` , `sys punch` , `sys handholding` , `sys kill` , `sys hold` , `sys pats` , `sys boop` , `sys snuggle` , `sys bully`"""

async def setup (client ):
    await client .add_cog (RoleplayHelp (client ))

"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
