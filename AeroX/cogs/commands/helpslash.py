import discord 
from discord .ext import commands 
from discord import app_commands ,Interaction 
from core import Context 
from core .Strelizia import Strelizia 
from core .Cog import Cog 
from utils .Tools import getConfig ,ignore_check ,blacklist_check 
from utils import help as vhelp 
import asyncio 

color =0x000000 

class HelpSlash (Cog ,name ="helpslash"):
    def __init__ (self ,client :Strelizia ):
        self .bot =client 

    def create_strelizia_mapping (self ,mapping ):
        """Create a filtered mapping that only includes cogs from cogs/strelizia directories"""
        strelizia_mapping ={}


        allowed_cog_classes ={

        '_general','_voice','_games','_welcome','ticket','__sticky','__boost',
        '_automod','_antinuke','_music','_extra','_fun','_moderation','_giveaway',

        '_leveling','_ai','_server','RoleplayHelp','VerificationHelp',
        '_tracking','_logging','_counting','_Backup','_crew','_ignore','eco'
        }

        for cog ,commands in mapping .items ():
            if cog and hasattr (cog ,'__class__'):
                cog_class_name =cog .__class__ .__name__ 

                if cog_class_name in allowed_cog_classes and hasattr (cog ,'help_custom'):
                    strelizia_mapping [cog ]=commands 

        return strelizia_mapping 

    @app_commands .command (name ="help",description ="Shows help about the bot and commands")
    async def help_slash (self ,interaction :Interaction ):
        """Slash command version of help - shows main help menu"""
        try :

            if interaction .guild :
                data =await getConfig (interaction .guild .id )
                prefix =data ["prefix"]
            else :
                prefix =">"


            await interaction .response .defer ()


            mapping ={}
            for cog in interaction .client .cogs .values ():
                if hasattr (cog ,'get_commands')and cog .get_commands ():
                    mapping [cog ]=cog .get_commands ()

            await asyncio .sleep (0.1 )


            embed =discord .Embed (
            title ="Help Menu",
            color =0x000000 
            )
            embed .set_image (url ="https://cdn.discordapp.com/banners/1372468860435042344/2200c89d12a45d8cf648694ad30535f8.png?size=512")

            embed .add_field (
            name ="<:home:1372530452681719950> __**General Features**__",
            value =">>> \n <:icon_volume:1372375121703997472> Voice\n"
            " <:icons_games:1372375167266721885> Games\n"
            " <:icon_welcome:1372375051483218071> Welcomer\n"
            " <:icon_ticket:1372375056893739019> Ticketing\n"
            " <:icon_edit:1372531753343778908> Auto Setup\n"
            " <:icon_autorole:1372532056344625213> Autorole\n"
            " <:icon_Extra:1372375162640535653> Fun\n"
            " <:icon_ignore:1372375104100765706> Ignore Channels\n"
            " <:logging_icons:1377373741268471900> Logging\n"
            " <:plus_icons:1377949309751791717> Counting\n"
            " <:leveling_icons:1378293065273442395> Leveling\n"
            " <:tracking_icons:1378293093219962921> Tracking\n"
            )

            embed .add_field (
            name ="<:icons_saturn:1372375229753593967> __**Bot Features**__",
            value =">>> \n <:icon_automod:1372375071750094949> Security\n"
            " <:icon_bot:1372375178033758270> Automod\n"
            " <:Icons_utility:1372374976577011763> Utility\n"
            " <:icon_music:1372375041542721638> Music\n"
            " <:icon_moderation:1372375066951553155> Moderation\n"
            " <:icon_categories:1372375027340804176> General\n"
            " <:icon_giveaway:1372375046332485663> Giveaway\n"
            " <:Ai:1375898214087135263> Artificial Intelligence\n"
            " <:backup_icons:1376857941986250844> Backup\n"
            " <:icons_tv:1381541359055540255> Roleplay\n"
            " <:staff_icons:1381539824711766046> Staff Application\n"
            )

            embed .set_footer (
            text =f"Requested By {interaction.user}",
            )

            embed .set_thumbnail (url =interaction .user .avatar .url if interaction .user .avatar else interaction .user .default_avatar .url )


            class FakeContext :
                def __init__ (self ,interaction ):
                    self .author =interaction .user 
                    self .guild =interaction .guild 
                    self .bot =interaction .client 
                    self .prefix ="/"
                    self .interaction =interaction 

            fake_ctx =FakeContext (interaction )


            mapping ={}
            for cog in self .bot .cogs .values ():
                if cog .get_commands ():
                    mapping [cog ]=cog .get_commands ()


            filtered_mapping =self .create_strelizia_mapping (mapping )


            view =vhelp .View (mapping =filtered_mapping ,
            ctx =fake_ctx ,
            homeembed =embed ,
            ui =2 )


            await interaction .edit_original_response (embed =embed ,view =view )

        except Exception as e :
            print (f"Error in slash help command: {e}")
            if not interaction .response .is_done ():
                await interaction .response .send_message (f"An error occurred: {str(e)}",ephemeral =True )
            else :
                await interaction .followup .send (f"An error occurred: {str(e)}",ephemeral =True )

async def setup (client ):
    await client .add_cog (HelpSlash (client ))

"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""

"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""