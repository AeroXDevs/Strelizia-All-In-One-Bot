import discord 
from discord .ext import commands 


class _general (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    """General commands"""

    def help_custom (self ):
              emoji ='<:icon_categories:1372375027340804176>'
              label ="General Commands"
              description =""
              return emoji ,label ,description 

    @commands .group ()
    async def __General__ (self ,ctx :commands .Context ):
        """`status` , `afk` , `avatar` , `banner` , `servericon` , `membercount` , `poll` , `hack` , `token` , `users` , `wizz` , `urban` , `rickroll` , `hash` , `snipe` , `users` , `list boosters` , `list inrole` , `list emojis` , `list bots` , `list admins` , `list invoice` , `list mods` , `list early` , `list activedeveloper` , `list createpos` , `list roles` , `calc`"""
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
