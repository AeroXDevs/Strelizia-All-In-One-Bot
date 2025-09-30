import discord 
from discord .utils import *
from core import Strelizia ,Cog 
from utils .Tools import getConfig 
from utils .config import BotName ,serverLink 
from discord .ext import commands 

class Autorole (Cog ):
    def __init__ (self ,bot :Strelizia ):
        self .bot =bot 

    @commands .Cog .listener (name ="on_guild_join")
    async def send_msg_to_adder (self ,guild :discord .Guild ):
        data =await getConfig (guild .id )
        prefix =data .get ("prefix","!")

        async for entry in guild .audit_logs (limit =3 ):
            if entry .action ==discord .AuditLogAction .bot_add :
                embed =discord .Embed (
                description =(
                f"<:icons_saturn:1372375229753593967> **Thanks for adding {BotName}!**\n\n"
                f"<a:GC_z_icon_rightarrow:1374279174751125534> My default prefix is `{prefix}`\n"
                f"<a:GC_z_icon_rightarrow:1374279174751125534> Use `{prefix}help` to see a list of commands\n"
                f"<a:GC_z_icon_rightarrow:1374279174751125534> For detailed guides, FAQ, and information, visit our "
                f"links below:\n"
                f"🔗 [Invite Me](https://discord.com/oauth2/authorize?client_id=1372468860435042344&permissions=8&integration_type=0&scope=bot+applications.commands) "
                f"| [Visit Website](https://landing.strelizia.space) "
                f"| [Support Server](https://discord.gg/JxCFmz9nZP)"
                ),
                color =0x0d0d0e 
                )

                avatar_url =entry .user .avatar .url if entry .user .avatar else entry .user .default_avatar .url 
                embed .set_thumbnail (url =avatar_url )

                if guild .icon :
                    embed .set_author (name =guild .name ,icon_url =guild .icon .url )
                else :
                    embed .set_author (name =guild .name )

                try :
                    await entry .user .send (embed =embed )
                except Exception as e :
                    print (f"Failed to send welcome message: {e}")
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
