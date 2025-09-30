import discord 
from discord .ext import commands 
import asyncio 

class React (commands .Cog ):

    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .Cog .listener ()
    async def on_message (self ,message ):
        if message .author .bot :
            return 
        for owner in self .bot .owner_ids :
            if f"<@{owner}>"in message .content :
                try :
                    if owner ==1124248109472550993 :

                        emojis =[
                        "<a:crown:1376599839290429512>",
                        "<a:ban:1376600344502468618>",
                        "<a:star:1376600544847593482>",
                        "<a:_rose:1367348649381859490>",
                        "<:land_yildiz:1367348419022295143>",
                        "<a:37496alert:1367348857914130434>",
                        "<:headmod:1367348948720816220>",
                        "<:AlphaEsportsBlack:1367349128647934044>",
                        "<a:GIFD:1275850452323401789>",
                        "<a:GIFN:1275850451212042391>",
                        "<a:max__A:1295014945641201685>",
                        "<:Heeriye:1274769360560328846>",
                        "<:heart_em:1274781856406962250>",
                        "<a:Star:1273588820373147803>",
                        "<a:crown:935613334491922472>",
                        "<:headmod:1274781954482376857>",
                        "<a:sg_rd:1273974278433280122> ",
                        "<a:RedHeart:1272229548280512547>",
                        " <a:star:1251876754516349059>"
                        ]
                        for emoji in emojis :
                            await message .add_reaction (emoji )
                    else :

                        await message .add_reaction ("<a:crown:935613334491922472>")
                except discord .errors .RateLimited as e :
                    await asyncio .sleep (e .retry_after )
                    await message .add_reaction ("<a:crown:935613334491922472>")
                except Exception as e :
                    print (f"An unexpected error occurred Auto react owner mention: {e}")

"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
