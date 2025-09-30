import discord 
from discord .ext import commands 

class _games (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    """Games commands"""

    def help_custom (self ):
		      emoji ='<:icons_games:1372375167266721885> '
		      label ="Games Commands"
		      description =""
		      return emoji ,label ,description 

    @commands .group ()
    async def __Games__ (self ,ctx :commands .Context ):
        """`blackjack` , `chess` , `tic-tac-toe` , `country-guesser` , `rps` , `lights-out` , `wordle` , `2048` , `memory-game` , `number-slider` , `battleship` , `connect-four` , `slots`"""
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
